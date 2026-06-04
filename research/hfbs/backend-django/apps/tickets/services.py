"""
apps/tickets/services.py — TicketService
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Генерация PDF-билета с помощью ReportLab.

Структура билета:
  - Название события, дата, место
  - QR-код (mock: просто текст)
  - Уникальный номер билета
  - Логотип HFBS
"""
import os
import uuid
import logging
from datetime import datetime

from django.conf import settings
from reportlab.lib.pagesizes import A5
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

from apps.analytics.event_service import EventService

logger = logging.getLogger(__name__)


class TicketService:

    @staticmethod
    def generate(order, payment_id: str) -> str:
        """
        Генерирует PDF-билет и сохраняет в media/tickets/.
        Возвращает URL для скачивания.
        """
        # Создаём директорию если нет
        tickets_dir = os.path.join(settings.MEDIA_ROOT, "tickets")
        os.makedirs(tickets_dir, exist_ok=True)

        ticket_id = str(uuid.uuid4())[:8].upper()
        filename  = f"ticket_{ticket_id}.pdf"
        filepath  = os.path.join(tickets_dir, filename)

        # ── ReportLab PDF ─────────────────────────────────────
        doc    = SimpleDocTemplate(filepath, pagesize=A5, topMargin=1*cm, bottomMargin=1*cm)
        styles = getSampleStyleSheet()
        story  = []

        # Заголовок
        title_style = ParagraphStyle(
            "TicketTitle",
            parent=styles["Title"],
            fontSize=22,
            textColor=colors.HexColor("#1a1a2e"),
            alignment=TA_CENTER,
        )
        story.append(Paragraph("🎟 HFBS TICKET", title_style))
        story.append(Spacer(1, 0.5*cm))

        # Информация о событии
        event = order.seat.event
        seat  = order.seat

        data = [
            ["Событие",    str(event.title)],
            ["Дата",       event.date.strftime("%d.%m.%Y %H:%M") if hasattr(event, "date") else "—"],
            ["Место",      f"Ряд {seat.row}, Место {seat.number}"],
            ["Категория",  seat.category.capitalize()],
            ["Цена",       f"${order.amount}"],
            ["Ticket ID",  ticket_id],
            ["Payment ID", payment_id[:8] + "..."],
            ["Дата покупки", datetime.now().strftime("%d.%m.%Y %H:%M")],
        ]

        table = Table(data, colWidths=[5*cm, 8*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (0, -1), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR",   (0, 0), (0, -1), colors.white),
            ("BACKGROUND",  (1, 0), (1, -1), colors.HexColor("#f0f4ff")),
            ("FONTSIZE",    (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (1, 0), (1, -1), [colors.HexColor("#f0f4ff"), colors.white]),
            ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",  (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.5*cm))

        # QR placeholder
        qr_style = ParagraphStyle("QR", parent=styles["Normal"], alignment=TA_CENTER, fontSize=9)
        story.append(Paragraph(f"[QR: {ticket_id}]", qr_style))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(
            '<font color="#888888" size="8">High-Frequency Booking System © 2025</font>',
            ParagraphStyle("Footer", parent=styles["Normal"], alignment=TA_CENTER),
        ))

        doc.build(story)

        # Публикуем событие
        EventService.publish("ticket", {
            "type":      "TICKET_GENERATED",
            "ticket_id": ticket_id,
            "order_id":  order.id,
            "filepath":  filepath,
        })

        logger.info("Ticket %s generated: %s", ticket_id, filepath)

        # Возвращаем относительный URL
        return f"/media/tickets/{filename}"
