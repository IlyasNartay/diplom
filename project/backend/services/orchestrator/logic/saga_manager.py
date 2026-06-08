import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.commands import (
    BookingStatus,
    CancelOrderCommand,
    CompleteOrderCommand,
    ConfirmSeatCommand,
    CreateOrderCommand,
    CreatePaymentCommand,
    GenerateTicketCommand,
    ReleaseSeatCommand,
    ReserveSeatCommand,
)
from common.custom_logger import get_correlation_id
from common.outbox.models import OutboxEvent
from services.catalog_service.models import Event, Session
from services.orchestrator.database import AsyncSessionLocal
from services.orchestrator.models import BookingSaga, SagaStatus
from services.seat_service.models import Seat

logger = logging.getLogger(__name__)


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


async def _load_event_enrichment_maps(
    db_session: AsyncSession, seat_ids: list[uuid.UUID]
) -> tuple[
    dict[uuid.UUID, uuid.UUID],
    dict[uuid.UUID, tuple[uuid.UUID, datetime, bool]],
    dict[uuid.UUID, tuple[str, bool]],
]:
    seat_to_session: dict[uuid.UUID, uuid.UUID] = {}
    if not seat_ids:
        return seat_to_session, {}, {}

    seat_res = await db_session.execute(select(Seat.id, Seat.session_id).where(Seat.id.in_(seat_ids)))
    for seat_id, session_id in seat_res.all():
        seat_to_session[seat_id] = session_id

    session_ids = list(set(seat_to_session.values()))
    session_info: dict[uuid.UUID, tuple[uuid.UUID, datetime, bool]] = {}
    if session_ids:
        sess_res = await db_session.execute(
            select(Session.id, Session.event_id, Session.start_time, Session.is_active).where(
                Session.id.in_(session_ids)
            )
        )
        for row in sess_res.all():
            session_info[row[0]] = (row[1], row[2], row[3])

    event_ids = list({t[0] for t in session_info.values()})
    event_info: dict[uuid.UUID, tuple[str, bool]] = {}
    if event_ids:
        ev_res = await db_session.execute(
            select(Event.id, Event.title, Event.is_active).where(Event.id.in_(event_ids))
        )
        for row in ev_res.all():
            event_info[row[0]] = (row[1], row[2])

    return seat_to_session, session_info, event_info


def _event_fields_for_first_seat(
    first_seat_id: uuid.UUID | None,
    seat_to_session: dict[uuid.UUID, uuid.UUID],
    session_info: dict[uuid.UUID, tuple[uuid.UUID, datetime, bool]],
    event_info: dict[uuid.UUID, tuple[str, bool]],
    now: datetime,
) -> tuple[str | None, bool | None, bool | None]:
    if not first_seat_id or first_seat_id not in seat_to_session:
        return None, None, None

    sess_id = seat_to_session[first_seat_id]
    if sess_id not in session_info:
        return None, None, None

    event_id, start_time, _sess_active = session_info[sess_id]
    event_title = None
    event_is_active = None
    if event_id in event_info:
        event_title, event_is_active = event_info[event_id]

    st = start_time
    if st.tzinfo is None:
        st = st.replace(tzinfo=timezone.utc)
    session_has_passed = st < now
    return event_title, event_is_active, session_has_passed


def _normalize_ticket_url(ticket_url: str | None) -> str | None:
    if not ticket_url:
        return None

    cleaned = ticket_url.strip()
    if not cleaned or cleaned == "No tickets":
        return None

    return cleaned


async def get_booking_status(booking_id: uuid.UUID, db_session) -> BookingStatus:
    result = await db_session.execute(select(BookingSaga).where(BookingSaga.id == booking_id))
    saga = result.scalar_one_or_none()

    if not saga:
        raise HTTPException(status_code=404, detail="Booking not found")

    first_seat = saga.seat_ids[0] if saga.seat_ids else None
    seat_to_session, session_info, event_info = await _load_event_enrichment_maps(
        db_session, [first_seat] if first_seat else []
    )
    now = datetime.now(timezone.utc)
    event_title, event_is_active, session_has_passed = _event_fields_for_first_seat(
        first_seat, seat_to_session, session_info, event_info, now
    )

    return BookingStatus(
        booking_id=saga.id,
        status=saga.status.value,
        seat_ids=saga.seat_ids,
        ticket_url=_normalize_ticket_url(saga.ticket_url),
        error_reason=saga.error_reason,
        event_title=event_title,
        event_is_active=event_is_active,
        session_has_passed=session_has_passed,
    )


async def get_my_history(x_user_id: uuid.UUID, db_session) -> list[dict]:
    stmt = select(BookingSaga).where(BookingSaga.user_id == x_user_id).order_by(desc(BookingSaga.created_at))
    logger.info(f"Fetching history for User ID: {x_user_id}")
    result = await db_session.execute(stmt)
    sagas = list(result.scalars().all())

    first_seat_by_booking: dict[uuid.UUID, uuid.UUID] = {}
    first_seat_ids: list[uuid.UUID] = []
    for saga in sagas:
        if saga.seat_ids:
            sid = saga.seat_ids[0]
            first_seat_by_booking[saga.id] = sid
            first_seat_ids.append(sid)

    seat_to_session, session_info, event_info = await _load_event_enrichment_maps(db_session, first_seat_ids)

    now = datetime.now(timezone.utc)

    history = []
    for saga in sagas:
        first_seat = first_seat_by_booking.get(saga.id)
        event_title, event_is_active, session_has_passed = _event_fields_for_first_seat(
            first_seat, seat_to_session, session_info, event_info, now
        )

        history.append(
            {
                "booking_id": saga.id,
                "seat_ids": saga.seat_ids,
                "status": saga.status.value,
                "ticket_url": _normalize_ticket_url(saga.ticket_url),
                "created_at": saga.created_at,
                "error_reason": saga.error_reason,
                "event_title": event_title,
                "event_is_active": event_is_active,
                "session_has_passed": session_has_passed,
            }
        )

    return history


class SagaManager:
    async def start_new_saga(self, user_id: uuid.UUID, seat_ids: List[uuid.UUID], db_session: AsyncSession) -> str:
        saga = BookingSaga(user_id=user_id, seat_ids=seat_ids, status=SagaStatus.started)
        db_session.add(saga)
        await db_session.flush()

        command = ReserveSeatCommand(booking_id=saga.id, seat_ids=seat_ids, user_id=user_id)
        _enqueue_event(db_session, "seat.commands", command.model_dump_json().encode("utf-8"))

        await db_session.commit()
        return str(saga.id)

    async def process_kafka_event(self, msg_value: bytes):
        try:
            data = json.loads(msg_value.decode("utf-8"))
            event_type = data.get("type")
            booking_id_str = data.get("booking_id")
            order_id_str = data.get("order_id") or None

            if not booking_id_str:
                return

            logger.info(f"Orchestrator logic: Processing {event_type}...")

            async with AsyncSessionLocal() as db:
                result = await db.execute(select(BookingSaga).where(BookingSaga.id == uuid.UUID(booking_id_str)))
                saga = result.scalar_one_or_none()

                if not saga:
                    logger.error(f"Saga {booking_id_str} not found")
                    return

                terminal_states = [SagaStatus.cancelled, SagaStatus.completed, SagaStatus.seat_reservation_failed]

                if saga.status in terminal_states:
                    logger.warning(f"Event {event_type} ignored: Saga {saga.id} is already in terminal state ({saga.status}).")

                    if event_type == "PaymentSucceeded":
                        logger.error(f"CRITICAL: Late payment for cancelled saga {saga.id}! Needs REFUND!")

                    return

                if event_type == "SeatReserved":
                    if saga.status != SagaStatus.started:
                        logger.warning(f"Event ignored: Saga is already in {saga.status}")
                        return

                    saga.status = SagaStatus.seat_reserved
                    total_price = data.get("total_price", 0)

                    cmd = CreateOrderCommand(
                        booking_id=saga.id, seat_ids=saga.seat_ids, user_id=saga.user_id, price=total_price
                    )
                    _enqueue_event(db, "order.commands", cmd.model_dump_json().encode("utf-8"))
                    await db.commit()
                    logger.info(f"Step 2: Order requested for {booking_id_str}")

                elif event_type == "SeatReservationFailed":
                    saga.status = SagaStatus.seat_reservation_failed
                    saga.error_reason = data.get("reason", "Unknown seat error")
                    await db.commit()
                    logger.info("Saga failed: Seat taken")

                elif event_type == "OrderCreated":
                    saga.status = SagaStatus.payment_pending

                    cmd = CreatePaymentCommand(
                        booking_id=saga.id,
                        order_id=uuid.UUID(data.get("order_id")),
                        amount=data.get("price", 0),
                        user_id=saga.user_id,
                    )
                    _enqueue_event(db, "payment.commands", cmd.model_dump_json().encode("utf-8"))
                    await db.commit()
                    logger.info(f"Step 3: Sent CreatePaymentCommand for {booking_id_str}")

                elif event_type == "PaymentSucceeded":
                    saga.status = SagaStatus.payment_success

                    cmd_seat = ConfirmSeatCommand(booking_id=saga.id, seat_ids=saga.seat_ids)
                    _enqueue_event(db, "seat.commands", cmd_seat.model_dump_json().encode("utf-8"))

                    cmd_order = CompleteOrderCommand(booking_id=saga.id, order_id=uuid.UUID(data.get("order_id")))
                    _enqueue_event(db, "order.commands", cmd_order.model_dump_json().encode("utf-8"))

                    await db.commit()
                    logger.info(f"Payment SUCCESS for {booking_id_str}. Sent ConfirmSeat & CompleteOrder.")

                elif event_type == "PaymentFailed":
                    saga.status = SagaStatus.payment_failed
                    saga.error_reason = data.get("reason", "Payment declined")

                    cmd_seat_rel = ReleaseSeatCommand(booking_id=saga.id, seat_ids=saga.seat_ids)
                    _enqueue_event(db, "seat.commands", cmd_seat_rel.model_dump_json().encode("utf-8"))

                    cmd_order_canc = CancelOrderCommand(
                        booking_id=saga.id,
                        reason=f"Rollback due to payment failure: {saga.error_reason}",
                    )
                    _enqueue_event(db, "order.commands", cmd_order_canc.model_dump_json().encode("utf-8"))

                    await db.commit()
                    logger.info(f"Payment FAILED for {booking_id_str}. Sent ReleaseSeat & CancelOrder (Rollback).")

                elif event_type == "SeatSold":
                    saga.is_seat_sold = True
                    self._maybe_enqueue_ticket(db, saga, order_id_str)
                    await db.commit()
                    logger.info(f"Seats {saga.seat_ids} are officially sold.")

                elif event_type == "OrderCompleted":
                    saga.is_order_completed = True
                    self._maybe_enqueue_ticket(db, saga, order_id_str)
                    await db.commit()
                    logger.info(f"Order for {booking_id_str} is completed.")

                elif event_type == "TicketIssued":
                    saga.status = SagaStatus.completed
                    urls = data.get("ticket_urls", [])
                    saga.ticket_url = ", ".join(urls) if urls else "No tickets"
                    await db.commit()
                    logger.info(f"SAGA COMPLETED! Ticket URL: {saga.ticket_url}")

        except Exception as e:
            logger.error(f"Error in SagaManager: {e}")

    @staticmethod
    def _maybe_enqueue_ticket(db: AsyncSession, saga: BookingSaga, order_id: str | None) -> None:
        if not (saga.is_seat_sold and saga.is_order_completed):
            return
        if saga.status == SagaStatus.completed:
            return
        if not order_id:
            logger.error(f"Cannot generate ticket for saga {saga.id}: order_id is missing.")
            return
        logger.info("Both Seat and Order are finalized! Requesting Ticket generation...")
        cmd = GenerateTicketCommand(
            booking_id=saga.id,
            order_id=uuid.UUID(order_id),
            user_id=saga.user_id,
            seat_ids=saga.seat_ids,
        )
        _enqueue_event(db, "ticket.commands", cmd.model_dump_json().encode("utf-8"))
