"""
routers/orders.py — Orders Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.security import get_current_user
from models.db_models import Order, Seat, SeatStatusEnum, OrderStatusEnum
from schemas.schemas import CreateOrderRequest, OrderOut
from services.event_service import AsyncEventService

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


@router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: CreateOrderRequest,
    db: AsyncSession = Depends(get_db),
    user: dict       = Depends(get_current_user),
):
    """Создаёт заказ для RESERVED места."""
    result = await db.execute(
        select(Seat).where(Seat.id == body.seat_id, Seat.status == 'RESERVED')
    )
    seat = result.scalar_one_or_none()
    if not seat:
        raise HTTPException(status_code=404, detail="Место не найдено или не забронировано")

    order = Order(
        user_id=user["user_id"],
        seat_id=body.seat_id,
        amount=seat.price,
        status=OrderStatusEnum.PENDING,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    await AsyncEventService.publish("order", {
        "type": "ORDER_CREATED", "order_id": order.id,
        "user_id": user["user_id"], "seat_id": body.seat_id,
    })

    return OrderOut(order_id=order.id, amount=order.amount, status=order.status)


@router.get("/{order_id}/", response_model=OrderOut)
async def order_detail(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict       = Depends(get_current_user),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == user["user_id"])
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return OrderOut(order_id=order.id, amount=order.amount, status=order.status, created_at=order.created_at)
