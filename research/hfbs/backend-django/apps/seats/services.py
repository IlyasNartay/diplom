"""
apps/seats/services.py — SeatService
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Главный сервис управления местами.

Ключевая задача: защита от race conditions при одновременной покупке
одного места несколькими пользователями (HIGH FREQUENCY BOOKING).

Механизм:
  1. Клиент выбирает место → reserve_seat()
  2. SeatService устанавливает Redis-блокировку (SETNX + EXPIRE)
     Ключ: seat_lock:{seat_id}  Значение: user_id  TTL: 300 сек
  3. Если блокировка успешна — меняем статус в БД на RESERVED
  4. После оплаты — release_seat_to_sold() (статус SOLD)
  5. Если TTL истёк — release_seat() возвращает FREE

ВАЖНО (для диплома): В отличие от FastAPI, здесь всё синхронно.
Django использует потоки + connection pooling для параллелизма.
"""
import logging
from django.core.cache import cache
from django.db import transaction
from django.conf import settings

from .models import Seat, SeatStatus
from apps.analytics.event_service import EventService

logger = logging.getLogger(__name__)

# Префикс ключа в Redis
LOCK_PREFIX = "seat_lock"


class SeatLockError(Exception):
    """Место уже занято другим пользователем."""


class SeatService:

    @staticmethod
    def _lock_key(seat_id: int) -> str:
        return f"{LOCK_PREFIX}:{seat_id}"

    # ── Reserve ──────────────────────────────────────────────
    @classmethod
    def reserve_seat(cls, seat_id: int, user_id: int) -> Seat:
        """
        Атомарно блокирует место в Redis и ставит RESERVED в PostgreSQL.

        Использует cache.add() — атомарная операция (SETNX + EXPIRE).
        Если место уже заблокировано → SeatLockError.

        Синхронный вариант: блокирует поток на время запроса к БД.
        """
        lock_key = cls._lock_key(seat_id)
        ttl = settings.SEAT_LOCK_TTL  # 300 сек по умолчанию

        # cache.add() — атомарный SETNX: вернёт True только если ключа нет
        acquired = cache.add(lock_key, str(user_id), timeout=ttl)
        if not acquired:
            # Кто держит блокировку?
            holder = cache.get(lock_key)
            logger.warning(
                "Seat %s already locked by user %s, requested by user %s",
                seat_id, holder, user_id,
            )
            raise SeatLockError(f"Место {seat_id} уже забронировано другим пользователем")

        try:
            # Обновляем статус в PostgreSQL внутри транзакции
            with transaction.atomic():
                seat = (
                    Seat.objects
                    .select_for_update()   # строчная блокировка на уровне БД
                    .get(id=seat_id, status=SeatStatus.FREE)
                )
                seat.status = SeatStatus.RESERVED
                seat.save(update_fields=["status"])

            # Публикуем событие в EventService (Kafka / mock)
            EventService.publish("seat", {
                "type":    "SEAT_RESERVED",
                "seat_id": seat_id,
                "user_id": user_id,
            })

            logger.info("Seat %s reserved by user %s", seat_id, user_id)
            return seat

        except Seat.DoesNotExist:
            # Место уже не FREE → откат Redis-блокировки
            cache.delete(lock_key)
            raise SeatLockError(f"Место {seat_id} уже не свободно")

        except Exception:
            # Любая ошибка → снимаем блокировку
            cache.delete(lock_key)
            raise

    # ── Sell ─────────────────────────────────────────────────
    @classmethod
    def mark_seat_sold(cls, seat_id: int, user_id: int) -> Seat:
        """
        Переводит место в SOLD после успешной оплаты.
        Снимает Redis-блокировку (место теперь окончательно занято).
        """
        with transaction.atomic():
            seat = (
                Seat.objects
                .select_for_update()
                .get(id=seat_id, status=SeatStatus.RESERVED)
            )
            seat.status = SeatStatus.SOLD
            seat.save(update_fields=["status"])

        # Удаляем Redis-ключ — место продано, блокировка больше не нужна
        cache.delete(cls._lock_key(seat_id))

        EventService.publish("seat", {
            "type":    "SEAT_SOLD",
            "seat_id": seat_id,
            "user_id": user_id,
        })

        logger.info("Seat %s sold to user %s", seat_id, user_id)
        return seat

    # ── Release ──────────────────────────────────────────────
    @classmethod
    def release_seat(cls, seat_id: int) -> None:
        """
        Возвращает место в FREE (например, если оплата не прошла
        или TTL Redis истёк и джобa вернула статус).
        """
        with transaction.atomic():
            Seat.objects.filter(
                id=seat_id,
                status=SeatStatus.RESERVED,
            ).update(status=SeatStatus.FREE)

        cache.delete(cls._lock_key(seat_id))

        EventService.publish("seat", {
            "type":    "SEAT_RELEASED",
            "seat_id": seat_id,
        })

    # ── Query helpers ─────────────────────────────────────────
    @staticmethod
    def get_seats_for_event(event_id: int):
        return (
            Seat.objects
            .filter(event_id=event_id)
            .order_by("row", "number")
            .values("id", "row", "number", "category", "price", "status")
        )
