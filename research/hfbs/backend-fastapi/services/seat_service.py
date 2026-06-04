"""
services/seat_service.py — Async SeatService (FastAPI)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
КЛЮЧЕВОЕ ОТЛИЧИЕ от Django (для диплома):

Django (sync):
    acquired = cache.add(lock_key, user_id, timeout=ttl)
    ↑ Блокирует поток на время TCP-запроса к Redis (~1-2ms)
    При 1000 RPS: 1000 заблокированных потоков → нужен большой thread pool

FastAPI (async):
    acquired = await redis.set(lock_key, user_id, nx=True, ex=ttl)
    ↑ НЕ блокирует event loop. Корутина "паузируется",
      другие запросы обрабатываются в это время.
    При 1000 RPS: 1 поток справляется с тысячами ожидающих корутин

Оба используют SET NX — атомарная операция Redis.
Защита от race condition одинакова. Разница — в масштабируемости.
"""
import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from models.db_models import Seat, SeatStatusEnum
from services.event_service import AsyncEventService
from core.config import settings

logger = logging.getLogger(__name__)

LOCK_PREFIX = "seat_lock"


class SeatLockError(Exception):
    """Место уже заблокировано."""


class AsyncSeatService:

    @staticmethod
    def _lock_key(seat_id: int) -> str:
        return f"{LOCK_PREFIX}:{seat_id}"

    # ── Reserve ──────────────────────────────────────────────
    @classmethod
    async def reserve_seat(
        cls,
        seat_id: int,
        user_id: int,
        db: AsyncSession,
        redis: aioredis.Redis,
    ) -> Seat:
        """
        Асинхронно блокирует место.

        SET NX (set if not exists) + EX (expire) — атомарная операция.
        Если ключ уже существует → Redis вернёт None → SeatLockError.

        await здесь означает: "передай управление event loop пока Redis отвечает".
        Другие запросы продолжают обрабатываться параллельно!
        """
        lock_key = cls._lock_key(seat_id)

        # Атомарная Redis-операция: SET key value NX EX ttl
        acquired = await redis.set(
            lock_key,
            str(user_id),
            nx=True,              # Only set if Not eXists
            ex=settings.seat_lock_ttl,
        )

        if not acquired:
            holder = await redis.get(lock_key)
            logger.warning(
                "Seat %s locked by user %s, requested by %s",
                seat_id, holder, user_id,
            )
            raise SeatLockError(f"Место {seat_id} уже забронировано другим пользователем")

        try:
            # SELECT ... FOR UPDATE — строчная блокировка в PostgreSQL
            # Также асинхронная! Не блокирует event loop.
            result = await db.execute(
                select(Seat)
                .where(Seat.id == seat_id, Seat.status == 'FREE')
                .with_for_update()
            )
            seat = result.scalar_one_or_none()

            if not seat:
                await redis.delete(lock_key)
                raise SeatLockError(f"Место {seat_id} уже не свободно")

            # Обновляем статус
            seat.status = 'RESERVED'
            await db.commit()
            await db.refresh(seat)

            # Публикуем событие (fire-and-forget, не блокируем ответ)
            await AsyncEventService.publish("seat", {
                "type":    "SEAT_RESERVED",
                "seat_id": seat_id,
                "user_id": user_id,
            })

            logger.info("Seat %s reserved by user %s (async)", seat_id, user_id)
            return seat

        except SeatLockError:
            raise
        except Exception:
            await redis.delete(lock_key)
            await db.rollback()
            raise

    # ── Sell ─────────────────────────────────────────────────
    @classmethod
    async def mark_seat_sold(
        cls,
        seat_id: int,
        user_id: int,
        db: AsyncSession,
        redis: aioredis.Redis,
    ) -> Seat:
        result = await db.execute(
            select(Seat)
            .where(Seat.id == seat_id, Seat.status == 'RESERVED')
            .with_for_update()
        )
        seat = result.scalar_one_or_none()
        if not seat:
            raise SeatLockError(f"Место {seat_id} не в статусе RESERVED")

        seat.status = 'SOLD'
        await db.commit()
        await redis.delete(cls._lock_key(seat_id))

        await AsyncEventService.publish("seat", {
            "type": "SEAT_SOLD", "seat_id": seat_id, "user_id": user_id,
        })
        return seat

    # ── Release ──────────────────────────────────────────────
    @classmethod
    async def release_seat(cls, seat_id: int, db: AsyncSession, redis: aioredis.Redis) -> None:
        await db.execute(
            update(Seat)
            .where(Seat.id == seat_id, Seat.status == 'RESERVED')
            .values(status=SeatStatusEnum.FREE)
        )
        await db.commit()
        await redis.delete(cls._lock_key(seat_id))
        await AsyncEventService.publish("seat", {"type": "SEAT_RELEASED", "seat_id": seat_id})

    # ── List ─────────────────────────────────────────────────
    @staticmethod
    async def get_seats_for_event(event_id: int, db: AsyncSession) -> list[Seat]:
        result = await db.execute(
            select(Seat)
            .where(Seat.event_id == event_id)
            .order_by(Seat.row, Seat.number)
        )
        return result.scalars().all()
