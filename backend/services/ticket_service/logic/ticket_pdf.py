import json
import os
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from services.ticket_service.config import settings

_FONT_BODY: str | None = None
_FONT_BOLD: str | None = None

# Палитра (кинотеатр / тёмная шапка + золотой акцент)
_COLOR_HEADER = (0.10, 0.16, 0.32)
_COLOR_GOLD = (0.78, 0.62, 0.22)
_COLOR_MUTED = (0.42, 0.45, 0.50)
_COLOR_TEXT = (0.12, 0.14, 0.18)
_COLOR_CARD_EDGE = (0.82, 0.86, 0.91)
_COLOR_SOFT_BG = (0.96, 0.97, 0.99)


def _register_fonts() -> tuple[str, str]:
    global _FONT_BODY, _FONT_BOLD
    if _FONT_BODY:
        assert _FONT_BOLD is not None
        return _FONT_BODY, _FONT_BOLD

    body_candidates: list[str] = []
    if (settings.TICKET_FONT_PATH or "").strip():
        body_candidates.append(settings.TICKET_FONT_PATH.strip())
    body_candidates.append("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if os.name == "nt":
        body_candidates.append(r"C:\Windows\Fonts\arial.ttf")

    bold_candidates: list[str] = []
    if (settings.TICKET_FONT_PATH or "").strip():
        p = Path(settings.TICKET_FONT_PATH.strip())
        bold_candidates.append(str(p.parent / "DejaVuSans-Bold.ttf"))
    bold_candidates.append("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if os.name == "nt":
        bold_candidates.append(r"C:\Windows\Fonts\arialbd.ttf")

    for path in body_candidates:
        if path and Path(path).is_file():
            pdfmetrics.registerFont(TTFont("TicketBody", path))
            _FONT_BODY = "TicketBody"
            break
    if not _FONT_BODY:
        _FONT_BODY = "Helvetica"

    for path in bold_candidates:
        if path and Path(path).is_file():
            pdfmetrics.registerFont(TTFont("TicketBold", path))
            _FONT_BOLD = "TicketBold"
            break
    if not _FONT_BOLD:
        _FONT_BOLD = "Helvetica-Bold"

    return _FONT_BODY, _FONT_BOLD


def _wrap_words(text: str, max_chars: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    cur = words[0]
    for w in words[1:]:
        if len(cur) + 1 + len(w) <= max_chars:
            cur = f"{cur} {w}"
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def _pretty_uuid(u: uuid.UUID) -> tuple[str, str]:
    """Короткая строка для глаз + полный UUID мелким шрифтом."""
    s = str(u)
    if len(s) >= 20:
        short = f"{s[:8]} … {s[-8:]}"
    else:
        short = s
    return short, s


def build_ticket_pdf(
    *,
    booking_id: uuid.UUID,
    order_id: uuid.UUID,
    event_title: str,
    hall_name: str,
    start_time: datetime | None,
    city_line: str,
    seat_lines: list[str],
) -> bytes:
    qr_payload = json.dumps(
        {
            "booking_id": str(booking_id),
            "order_id": str(order_id),
            "v": 1,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=4, border=2)
    qr.add_data(qr_payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a2744", back_color="white")
    qr_buf = BytesIO()
    img.save(qr_buf, format="PNG")
    qr_buf.seek(0)

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    body, bold = _register_fonts()

    margin = 14 * mm
    header_h = 28 * mm
    qr_size = 48 * mm
    qr_pad = 3 * mm

    # Лёгкий фон страницы
    c.saveState()
    c.setFillColorRGB(*_COLOR_SOFT_BG)
    c.rect(0, 0, w, h, fill=1, stroke=0)
    c.restoreState()

    # Шапка
    c.saveState()
    c.setFillColorRGB(*_COLOR_HEADER)
    c.rect(0, h - header_h, w, header_h, fill=1, stroke=0)
    c.setFillColorRGB(*_COLOR_GOLD)
    c.rect(0, h - header_h, w, 1.2 * mm, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont(bold, 24)
    c.drawString(margin, h - 17 * mm, "TicketON")
    c.setFont(body, 11)
    c.setFillColorRGB(0.78, 0.82, 0.92)
    c.drawRightString(w - margin, h - 14 * mm, "ЭЛЕКТРОННЫЙ БИЛЕТ")
    c.restoreState()

    content_top = h - header_h - 10 * mm
    qr_x = w - margin - qr_size - 2 * qr_pad
    qr_y = content_top - qr_size - 2 * qr_pad
    left_w = qr_x - margin - 10 * mm

    # «Карточка» билета
    card_margin = 10 * mm
    card_bottom = 22 * mm
    c.saveState()
    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(*_COLOR_CARD_EDGE)
    c.setLineWidth(0.8)
    c.roundRect(
        card_margin,
        card_bottom,
        w - 2 * card_margin,
        content_top - card_bottom + 4 * mm,
        5 * mm,
        fill=1,
        stroke=1,
    )
    c.restoreState()

    inner_left = margin + 6 * mm
    y = content_top - 4 * mm

    # Название события
    c.setFillColorRGB(*_COLOR_HEADER)
    c.setFont(bold, 17)
    for line in _wrap_words(event_title, max(12, int(left_w / (4.2 * mm)))):
        c.drawString(inner_left, y, line)
        y -= 7 * mm

    y -= 3 * mm

    def row(label: str, value: str, value_size: int = 11) -> None:
        nonlocal y
        c.setFillColorRGB(*_COLOR_MUTED)
        c.setFont(body, 8.5)
        c.drawString(inner_left, y, label.upper())
        y -= 4.2 * mm
        c.setFillColorRGB(*_COLOR_TEXT)
        c.setFont(body, value_size)
        for part in _wrap_words(value, max(10, int(left_w / (3.2 * mm)))):
            c.drawString(inner_left, y, part)
            y -= 5.2 * mm
        y -= 2 * mm

    if city_line:
        row("Город", city_line)
    if start_time:
        row("Дата и время", start_time.strftime("%d.%m.%Y  ·  %H:%M"))
    row("Зал", hall_name)

    # Места — в мягком блоке
    c.setFillColorRGB(*_COLOR_MUTED)
    c.setFont(body, 8.5)
    c.drawString(inner_left, y, "МЕСТА")
    y -= 5 * mm
    block_h = 7 * mm * max(1, len(seat_lines)) + 6 * mm
    c.saveState()
    c.setFillColorRGB(0.97, 0.98, 1.0)
    c.setStrokeColorRGB(*_COLOR_CARD_EDGE)
    c.setLineWidth(0.5)
    c.roundRect(inner_left, y - block_h + 2 * mm, left_w, block_h, 3 * mm, fill=1, stroke=1)
    c.restoreState()
    ty = y - 6 * mm
    c.setFillColorRGB(*_COLOR_TEXT)
    c.setFont(body, 12)
    for s in seat_lines:
        c.drawString(inner_left + 5 * mm, ty, f"•  {s}")
        ty -= 6.5 * mm
    y = y - block_h - 3 * mm

    # QR в рамке
    c.saveState()
    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(*_COLOR_CARD_EDGE)
    c.setLineWidth(0.9)
    c.roundRect(qr_x - qr_pad, qr_y - qr_pad, qr_size + 2 * qr_pad, qr_size + 2 * qr_pad, 3.5 * mm, fill=1, stroke=1)
    c.drawImage(ImageReader(qr_buf), qr_x, qr_y, width=qr_size, height=qr_size, mask="auto")
    c.setFillColorRGB(*_COLOR_MUTED)
    c.setFont(body, 7.5)
    c.drawCentredString(qr_x + qr_size / 2, qr_y - 5 * mm, "Контроль при входе")
    c.restoreState()

    # Нижний блок: бронирование и заказ
    foot_top = 52 * mm
    c.saveState()
    c.setStrokeColorRGB(*_COLOR_CARD_EDGE)
    c.setLineWidth(0.6)
    c.line(margin + 4 * mm, foot_top, w - margin - 4 * mm, foot_top)
    c.restoreState()

    fy = foot_top - 8 * mm
    b_short, b_full = _pretty_uuid(booking_id)
    o_short, o_full = _pretty_uuid(order_id)

    c.setFillColorRGB(*_COLOR_MUTED)
    c.setFont(body, 8)
    c.drawString(inner_left, fy, "Номер бронирования")
    fy -= 4.5 * mm
    c.setFillColorRGB(*_COLOR_HEADER)
    c.setFont(bold, 11)
    c.drawString(inner_left, fy, b_short)
    fy -= 4 * mm
    c.setFillColorRGB(*_COLOR_MUTED)
    c.setFont(body, 7)
    for chunk in _wrap_words(b_full, 52):
        c.drawString(inner_left, fy, chunk)
        fy -= 3.2 * mm

    fy -= 3 * mm
    c.setFillColorRGB(*_COLOR_MUTED)
    c.setFont(body, 8)
    c.drawString(inner_left, fy, "Заказ")
    fy -= 4.5 * mm
    c.setFillColorRGB(*_COLOR_HEADER)
    c.setFont(bold, 11)
    c.drawString(inner_left, fy, o_short)
    fy -= 4 * mm
    c.setFillColorRGB(*_COLOR_MUTED)
    c.setFont(body, 7)
    for chunk in _wrap_words(o_full, 52):
        c.drawString(inner_left, fy, chunk)
        fy -= 3.2 * mm

    c.setFillColorRGB(*_COLOR_MUTED)
    c.setFont(body, 8.5)
    c.drawCentredString(w / 2, 12 * mm, "Предъявите QR-код контролёру или на турникете")
    c.setFont(body, 7.5)
    c.drawCentredString(w / 2, 7 * mm, "Билет действителен на указанные места и сеанс  ·  TicketON")

    c.showPage()
    c.save()
    return buf.getvalue()


def save_ticket_pdf_file(booking_id: uuid.UUID, pdf_bytes: bytes) -> str:
    """Сохраняет PDF и возвращает публичный URL (или относительный /tickets/...)."""
    root = Path(settings.TICKETS_MEDIA_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    name = f"{booking_id}.pdf"
    (root / name).write_bytes(pdf_bytes)
    rel = f"/tickets/{name}"
    base = (settings.PUBLIC_TICKET_BASE_URL or "").rstrip("/")
    if base:
        return f"{base}{rel}"
    return rel
