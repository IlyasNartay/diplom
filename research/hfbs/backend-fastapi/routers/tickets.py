import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.security import get_current_user
from models.db_models import Order
from services.ticket_service import MEDIA_DIR

router = APIRouter(prefix="/api/v1/tickets", tags=["Tickets"])


@router.get("/{order_id}/", summary="Скачать PDF билет")
async def download_ticket(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict       = Depends(get_current_user),
):
    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == user["user_id"],
            Order.status == 'PAID',
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Оплаченный заказ не найден")

    if not os.path.exists(MEDIA_DIR):
        raise HTTPException(status_code=404, detail="Билеты ещё не сгенерированы")

    files = sorted([f for f in os.listdir(MEDIA_DIR) if f.endswith(".pdf")])
    if not files:
        raise HTTPException(status_code=404, detail="PDF билет не найден")

    filepath = os.path.join(MEDIA_DIR, files[-1])
    return FileResponse(
        path=filepath,
        media_type="application/pdf",
        filename=files[-1],
    )
