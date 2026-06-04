"""
services/ticket_service.py — Async TicketService (FastAPI)
Генерация PDF идентична Django-версии (ReportLab синхронный).
В продакшне: asyncio.run_in_executor() чтобы не блокировать event loop.
"""
import os
import uuid
import asyncio
import logging
from datetime import datetime
from functools import partial

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from reportlab.lib.pagesizes import A5
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

from models.db_models import Seat, Event
from services.event_service import AsyncEventService

logger = logging.getLogger(__name__)

MEDIA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media", "tickets")


def _build_pdf(filepath: str, event_title: str, event_date: str,
               seat_row: int, seat_num: int, seat_cat: str,
               amount: str, ticket_id: str, payment_id: str) -> None:
    """
    Синхронная генерация PDF (ReportLab не поддерживает async).
    Вызывается через run_in_executor чтобы не блокировать event loop.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    doc    = SimpleDocTemplate(filepath, pagesize=A5, topMargin=1*cm, bottomMargin=1*cm)
    styles = getSampleStyleSheet()
    story  = []

    title_style = ParagraphStyle(
        "TT", parent=styles["Title"], fontSize=22,
        textColor=colors.HexColor("#16213e"), alignment=TA_CENTER,
    )
    story.append(Paragraph("🎟 HFBS TICKET", title_style))
    story.append(Spacer(1, 0.5*cm))

    data = [
        ["Событие",    event_title],
        ["Дата",       event_date],
        ["Место",      f"Ряд {seat_row}, Место {seat_num}"],
        ["Категория",  seat_cat.capitalize()],
        ["Цена",       f"${amount}"],
        ["Ticket ID",  ticket_id],
        ["Payment ID", payment_id[:8] + "..."],
        ["Куплено",    datetime.now().strftime("%d.%m.%Y %H:%M")],
        ["Backend",    "FastAPI (async) ⚡"],
    ]

    table = Table(data, colWidths=[5*cm, 8*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (0, -1), colors.HexColor("#16213e")),
        ("TEXTCOLOR",   (0, 0), (0, -1), colors.white),
        ("BACKGROUND",  (1, 0), (1, -1), colors.HexColor("#eaf0ff")),
        ("FONTSIZE",    (0, 0), (-1, -1), 10),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(
        f'<font color="#888888" size="8">[QR: {ticket_id}] — HFBS © 2025</font>',
        ParagraphStyle("F", parent=styles["Normal"], alignment=TA_CENTER),
    ))
    doc.build(story)


class AsyncTicketService:

    @staticmethod
    async def generate(order, payment_id: str, db: AsyncSession) -> str:
        # Загружаем связанные объекты
        result = await db.execute(select(Seat).where(Seat.id == order.seat_id))
        seat = result.scalar_one()
        result = await db.execute(select(Event).where(Event.id == seat.event_id))
        event = result.scalar_one()

        ticket_id = str(uuid.uuid4())[:8].upper()
        filename  = f"ticket_{ticket_id}.pdf"
        filepath  = os.path.join(MEDIA_DIR, filename)

        # Запускаем синхронный PDF в thread pool (не блокируем event loop!)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,  # Использует ThreadPoolExecutor по умолчанию
            partial(
                _build_pdf,
                filepath,
                event.title,
                event.date.strftime("%d.%m.%Y %H:%M") if event.date else "—",
                seat.row, seat.number, seat.category,
                str(order.amount), ticket_id, payment_id,
            )
        )

        await AsyncEventService.publish("ticket", {
            "type": "TICKET_GENERATED", "ticket_id": ticket_id, "order_id": order.id,
        })
        logger.info("Async ticket %s generated", ticket_id)

        return f"/media/tickets/{filename}"
