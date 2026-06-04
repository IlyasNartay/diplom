"""
services/payment_service.py — Async PaymentService (FastAPI)
"""
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis

from models.db_models import Order, OrderStatusEnum
from services.seat_service import AsyncSeatService
from services.event_service import AsyncEventService
from services.ticket_service import AsyncTicketService

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    pass


class AsyncPaymentService:

    @classmethod
    async def process_payment(
        cls,
        order_id: int,
        card_token: str,
        user_id: int,
        db: AsyncSession,
        redis: aioredis.Redis,
    ) -> dict:
        """
        Асинхронная обработка платежа.

        Все await-точки не блокируют event loop:
          - await db.execute(...)   → PostgreSQL запрос
          - await redis.delete(...) → Redis команда
          - await ticket_service... → генерация PDF (I/O)
          - await publish(...)      → Kafka publish

        В Django эквивалентный код занял бы поток на ~50-100ms.
        FastAPI обрабатывает другие запросы в это время.
        """
        # Загружаем заказ
        result = await db.execute(
            select(Order)
            .where(Order.id == order_id, Order.status == 'PENDING')
        )
        order = result.scalar_one_or_none()
        if not order:
            raise PaymentError(f"Заказ #{order_id} не найден или уже оплачен")

        # Mock payment gateway
        payment_id = str(uuid.uuid4())
        logger.info("Async mock payment %s for order %s", payment_id, order_id)

        # Атомарное обновление в транзакции
        order.status = 'PAID'
        await db.flush()  # Фиксируем в рамках транзакции

        # Помечаем место как SOLD
        await AsyncSeatService.mark_seat_sold(
            seat_id=order.seat_id,
            user_id=user_id,
            db=db,
            redis=redis,
        )

        await db.commit()

        # Генерируем PDF
        ticket_url = await AsyncTicketService.generate(
            order=order, payment_id=payment_id, db=db,
        )

        # Публикуем событие
        await AsyncEventService.publish("payment", {
            "type":       "PAYMENT_SUCCESS",
            "order_id":   order_id,
            "payment_id": payment_id,
            "user_id":    user_id,
            "amount":     str(order.amount),
        })

        return {
            "payment_id": payment_id,
            "order_id":   order_id,
            "ticket_url": ticket_url,
        }
