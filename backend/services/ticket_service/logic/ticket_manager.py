import asyncio
import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.commands import GenerateTicketCommand
from common.custom_logger import get_correlation_id
from common.events import TicketIssuedEvent
from common.outbox.models import OutboxEvent
from services.ticket_service.database import AsyncSessionLocal
from services.ticket_service.logic.booking_details import load_show_context_for_seats
from services.ticket_service.logic.ticket_pdf import build_ticket_pdf, save_ticket_pdf_file
from services.ticket_service.models import Ticket

logger = logging.getLogger(__name__)


def _outbox_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    corr_id = get_correlation_id()
    if corr_id:
        headers["X-Request-ID"] = corr_id
    return headers


def _enqueue_event(db: AsyncSession, topic: str, payload_bytes: bytes) -> None:
    db.add(
        OutboxEvent(
            topic=topic,
            payload=payload_bytes.decode("utf-8"),
            headers=_outbox_headers(),
        )
    )


class TicketManager:
    async def process_kafka_message(self, msg_value: bytes):
        try:
            data = json.loads(msg_value.decode("utf-8"))
            if data.get("type") != "GenerateTicket":
                return

            cmd = GenerateTicketCommand(**data)
            logger.info("Generating ticket PDF for booking %s...", cmd.booking_id)

            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Ticket).where(Ticket.booking_id == cmd.booking_id))
                existing_ticket = result.scalar_one_or_none()

                if existing_ticket:
                    logger.info(
                        "Idempotency: ticket for booking %s exists, re-emitting TicketIssued",
                        cmd.booking_id,
                    )
                    evt = TicketIssuedEvent(booking_id=cmd.booking_id, ticket_urls=[existing_ticket.ticket_url])
                    _enqueue_event(db, "ticket.events", evt.model_dump_json().encode("utf-8"))
                    await db.commit()
                    return

                ctx = await load_show_context_for_seats(db, list(cmd.seat_ids))
                if ctx is None:
                    ctx = {
                        "event_title": "Мероприятие",
                        "hall_name": "—",
                        "start_time": None,
                        "city_line": "",
                        "seat_lines": [str(sid) for sid in cmd.seat_ids],
                    }

                pdf_bytes = await asyncio.to_thread(
                    build_ticket_pdf,
                    booking_id=cmd.booking_id,
                    order_id=cmd.order_id,
                    event_title=ctx["event_title"],
                    hall_name=ctx["hall_name"],
                    start_time=ctx["start_time"],
                    city_line=ctx["city_line"],
                    seat_lines=ctx["seat_lines"],
                )
                ticket_url = await asyncio.to_thread(save_ticket_pdf_file, cmd.booking_id, pdf_bytes)

                new_ticket = Ticket(booking_id=cmd.booking_id, user_id=cmd.user_id, ticket_url=ticket_url)
                db.add(new_ticket)

                evt = TicketIssuedEvent(booking_id=cmd.booking_id, ticket_urls=[ticket_url])
                _enqueue_event(db, "ticket.events", evt.model_dump_json().encode("utf-8"))
                await db.commit()

                logger.info("Ticket PDF saved: %s", ticket_url)

        except Exception as e:
            logger.error("Error in TicketManager: %s", e)
