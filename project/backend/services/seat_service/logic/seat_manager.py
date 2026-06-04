import json
import logging
import uuid
from typing import List

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.commands import (
    ConfirmSeatCommand,
    ReleaseSeatCommand,
    ReserveSeatCommand,
)
from common.errors import CommunicationError, EventNotFound
from common.events import SeatReleasedEvent, SeatReservationFailedEvent, SeatReservedEvent, SeatSoldEvent
from common.custom_logger import get_correlation_id
from common.outbox.models import OutboxEvent
from services.seat_service.database import AsyncSessionLocal
from services.seat_service.models import Seat, SeatStatus
from services.seat_service.schemas import SeatResponse

logger = logging.getLogger(__name__)


async def get_all_seats(session_id: uuid.UUID, db_session) -> List[SeatResponse]:
    stmt = select(Seat).where(Seat.session_id == session_id).order_by(Seat.row, Seat.number)
    result = await db_session.execute(stmt)
    seats = result.scalars().all()
    return [SeatResponse.model_validate(seat) for seat in seats]


async def generate_seats(session_id: uuid.UUID, rows: int, seats_per_row: int, db_session) -> int:
    catalog_url = f"http://catalog_service:8000/api/sessions/{str(session_id)}"
    logger.info(f"Checking Session in Catalog: {catalog_url}")

    async with httpx.AsyncClient() as client:
        try:
            headers = {}
            correlation_id = get_correlation_id()
            if correlation_id:
                headers["X-Request-ID"] = correlation_id
            response = await client.get(catalog_url, timeout=5.0, headers=headers)
            logger.info(f"Catalog Response: Code={response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Network Error calling Catalog: {e}")
            raise CommunicationError()

        if response.status_code != 200:
            logger.error(f"Session check failed! Status {response.status_code}. Aborting generation.")
            raise EventNotFound()

    session_payload = response.json()
    session_price = int(session_payload.get("price", 5000))

    logger.info(f"Session found. Generating {rows * seats_per_row} seats...")

    new_seats = []
    for r in range(1, rows + 1):
        for n in range(1, seats_per_row + 1):
            seat = Seat(session_id=session_id, row=str(r), number=str(n), status=SeatStatus.free, price=session_price)
            new_seats.append(seat)

    db_session.add_all(new_seats)
    await db_session.commit()
    return len(new_seats)


async def sync_seat_prices_for_session(session_id: uuid.UUID, price: int, db_session) -> int:
    stmt = update(Seat).where(Seat.session_id == session_id).values(price=price)
    result = await db_session.execute(stmt)
    await db_session.commit()
    return int(result.rowcount or 0)


def _outbox_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    corr_id = get_correlation_id()
    if corr_id:
        headers["X-Request-ID"] = corr_id
    return headers


def _enqueue_event(db: AsyncSession, topic: str, payload_bytes: bytes) -> None:
    db.add(OutboxEvent(
        topic=topic,
        payload=payload_bytes.decode("utf-8"),
        headers=_outbox_headers(),
    ))


class SeatManager:
    def __init__(self, redis):
        self.redis = redis

    async def process_kafka_message(self, msg_value: bytes):
        try:
            data = json.loads(msg_value.decode("utf-8"))
            msg_type = data.get("type")

            if msg_type == "ReserveSeat":
                await self._handle_reserve(data)
            elif msg_type == "ConfirmSeat":
                await self._handle_confirm(data)
            elif msg_type == "ReleaseSeat":
                await self._handle_release(data)

        except Exception as e:
            logger.error(f"Error in SeatManager: {e}")

    async def _handle_reserve(self, data: dict):
        cmd = ReserveSeatCommand(**data)
        logger.info(f"Reserving seats {cmd.seat_ids} for booking {cmd.booking_id}")

        locked_redis_keys: list[str] = []
        lock_failed = False

        for seat_id in cmd.seat_ids:
            lock_key = f"lock:seat:{seat_id}"
            is_locked = await self.redis.set(lock_key, str(cmd.booking_id), nx=True, ex=300)

            if is_locked:
                locked_redis_keys.append(lock_key)
            else:
                existing_owner = await self.redis.get(lock_key)
                if existing_owner == str(cmd.booking_id):
                    locked_redis_keys.append(lock_key)
                    continue
                lock_failed = True
                break

        if lock_failed:
            if locked_redis_keys:
                await self.redis.delete(*locked_redis_keys)
            if await self._is_already_reserved_by(cmd):
                return
            await self._send_fail(cmd, "SOME_SEATS_ALREADY_LOCKED")
            return

        async with AsyncSessionLocal() as db:
            stmt = select(Seat).where(Seat.id.in_(cmd.seat_ids))
            result = await db.execute(stmt)
            seats = result.scalars().all()

            if len(seats) != len(cmd.seat_ids):
                await self.redis.delete(*locked_redis_keys)
                await self._send_fail(cmd, "SOME_SEATS_NOT_FOUND")
                return

            already_reserved_by_us = all(
                s.status == SeatStatus.reserved and s.booking_id == str(cmd.booking_id) for s in seats
            )
            if already_reserved_by_us:
                logger.info(f"Idempotency: seats already reserved for booking {cmd.booking_id}. Re-emitting success.")
                total_price = sum(s.price for s in seats)
                event = SeatReservedEvent(booking_id=cmd.booking_id, seat_ids=cmd.seat_ids, total_price=total_price)
                _enqueue_event(db, "seat.events", event.model_dump_json().encode("utf-8"))
                await db.commit()
                return

            for seat in seats:
                if seat.status != SeatStatus.free:
                    await self.redis.delete(*locked_redis_keys)
                    await self._send_fail(cmd, "SOME_SEATS_NOT_FREE_IN_DB")
                    return

            total_price = sum(seat.price for seat in seats)

            for seat in seats:
                seat.status = SeatStatus.reserved
                seat.booking_id = str(cmd.booking_id)

            event = SeatReservedEvent(booking_id=cmd.booking_id, seat_ids=cmd.seat_ids, total_price=total_price)
            _enqueue_event(db, "seat.events", event.model_dump_json().encode("utf-8"))
            await db.commit()
            logger.info(f"Successfully reserved {len(seats)} seats. Total Price: {total_price}")

    async def _handle_confirm(self, data: dict):
        cmd = ConfirmSeatCommand(**data)
        async with AsyncSessionLocal() as db:
            stmt = select(Seat).where(Seat.id.in_(cmd.seat_ids))
            result = await db.execute(stmt)
            seats = result.scalars().all()

            for seat in seats:
                if seat.status == SeatStatus.sold:
                    logger.info(f"Idempotency: Seat {seat.id} is already SOLD.")
                    continue
                if seat.status == SeatStatus.free:
                    logger.error(f"CRITICAL: Trying to sell a FREE seat {seat.id}! It was rolled back.")
                    continue
                if seat.status == SeatStatus.reserved:
                    seat.status = SeatStatus.sold

            event = SeatSoldEvent(booking_id=cmd.booking_id, seat_ids=cmd.seat_ids)
            _enqueue_event(db, "seat.events", event.model_dump_json().encode("utf-8"))
            await db.commit()
            logger.info(f"Seats {cmd.seat_ids} are officially SOLD!")

    async def _handle_release(self, data: dict):
        cmd = ReleaseSeatCommand(**data)
        async with AsyncSessionLocal() as db:
            stmt = select(Seat).where(Seat.id.in_(cmd.seat_ids))
            result = await db.execute(stmt)
            seats = result.scalars().all()

            keys_to_delete = []

            for seat in seats:
                if seat.status == SeatStatus.free:
                    logger.info(f"Idempotency: Seat {seat.id} is already FREE. Skipping.")
                    continue
                if seat.status == SeatStatus.sold:
                    logger.error(f"CRITICAL: Trying to release a SOLD seat {seat.id}! Ignoring rollback.")
                    continue
                if seat.status == SeatStatus.reserved:
                    seat.status = SeatStatus.free
                    seat.booking_id = None
                    keys_to_delete.append(f"lock:seat:{seat.id}")

            event = SeatReleasedEvent(booking_id=cmd.booking_id, seat_ids=cmd.seat_ids)
            _enqueue_event(db, "seat.events", event.model_dump_json().encode("utf-8"))
            await db.commit()
            logger.info(f"Seats {cmd.seat_ids} RELEASED and FREE again!")

            if keys_to_delete:
                await self.redis.delete(*keys_to_delete)

    async def _is_already_reserved_by(self, cmd: ReserveSeatCommand) -> bool:
        async with AsyncSessionLocal() as db:
            stmt = select(Seat).where(Seat.id.in_(cmd.seat_ids))
            result = await db.execute(stmt)
            seats = result.scalars().all()

            if len(seats) != len(cmd.seat_ids):
                return False

            if all(s.status == SeatStatus.reserved and s.booking_id == str(cmd.booking_id) for s in seats):
                logger.info(f"Idempotency: seats already reserved for booking {cmd.booking_id}. Re-emitting success.")
                total_price = sum(s.price for s in seats)
                event = SeatReservedEvent(booking_id=cmd.booking_id, seat_ids=cmd.seat_ids, total_price=total_price)
                _enqueue_event(db, "seat.events", event.model_dump_json().encode("utf-8"))
                await db.commit()
                return True

            return False

    async def _send_fail(self, cmd: ReserveSeatCommand, reason: str):
        async with AsyncSessionLocal() as db:
            evt = SeatReservationFailedEvent(booking_id=cmd.booking_id, seat_ids=cmd.seat_ids, reason=reason)
            _enqueue_event(db, "seat.events", evt.model_dump_json().encode("utf-8"))
            await db.commit()
