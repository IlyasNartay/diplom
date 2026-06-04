"""
routers/payments.py — Payments Router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from core.database import get_db
from core.redis import get_redis
from core.security import get_current_user
from services.payment_service import AsyncPaymentService, PaymentError
from schemas.schemas import PaymentRequest, PaymentResponse

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


@router.post("/", response_model=PaymentResponse, summary="Обработать оплату")
async def process_payment(
    body: PaymentRequest,
    db: AsyncSession      = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    user: dict            = Depends(get_current_user),
):
    """
    Принимает оплату, переводит заказ в PAID, место в SOLD.
    Генерирует PDF-билет.
    """
    try:
        result = await AsyncPaymentService.process_payment(
            order_id=body.order_id,
            card_token=body.card_token,
            user_id=user["user_id"],
            db=db,
            redis=redis,
        )
        return PaymentResponse(**result)
    except PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e))
