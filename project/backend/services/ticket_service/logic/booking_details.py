import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from services.catalog_service.models import Event, Session as ShowSession
from services.seat_service.models import Seat

logger = logging.getLogger(__name__)


async def load_show_context_for_seats(db: AsyncSession, seat_ids: list[uuid.UUID]) -> dict | None:
    """Данные сеанса и мест для текста на билете. None, если места не найдены."""
    if not seat_ids:
        return None
    res = await db.execute(select(Seat).where(Seat.id.in_(seat_ids)))
    seats = res.scalars().all()
    if not seats:
        return None
    session_id = seats[0].session_id
    if any(s.session_id != session_id for s in seats):
        logger.warning(
            "Seats belong to different sessions; ticket PDF will use session %s only",
            session_id,
        )
        seats = [s for s in seats if s.session_id == session_id]

    seats_sorted = sorted(seats, key=lambda s: (s.row, s.number))
    seat_lines = [f"Ряд {s.row}, место {s.number}" for s in seats_sorted]

    show_res = await db.execute(
        select(ShowSession)
        .where(ShowSession.id == session_id)
        .options(selectinload(ShowSession.event).selectinload(Event.city))
    )
    show = show_res.scalar_one_or_none()
    if not show or not show.event:
        return {
            "event_title": "Мероприятие",
            "hall_name": "—",
            "start_time": None,
            "city_line": "",
            "seat_lines": seat_lines,
        }

    ev = show.event
    city_line = ""
    if ev.city:
        city_line = f"{ev.city.name_ru}"

    return {
        "event_title": ev.title,
        "hall_name": show.hall_name,
        "start_time": show.start_time,
        "city_line": city_line,
        "seat_lines": seat_lines,
    }
