"""
apps/payments/services.py — PaymentService
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mock-реализация платёжного шлюза.

В реальной системе здесь был бы вызов к Stripe / PayPal / ЮKassa.
Для диплома имитируем успешную оплату.

Транзакционность:
  - Order.status = PAID
  - Seat.status = SOLD
  Оба изменения — в одной БД-транзакции (atomicity).
"""
import logging
import uuid
from django.db import transaction

from apps.orders.models import Order, OrderStatus
from apps.seats.services import SeatService
from apps.analytics.event_service import EventService
from apps.tickets.services import TicketService

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    pass


class PaymentService:

    @classmethod
    def process_payment(cls, order_id: int, card_token: str) -> dict:
        """
        Обрабатывает оплату:
          1. Валидируем заказ
          2. Mock-вызов к платёжному шлюзу
          3. В транзакции: помечаем Order=PAID, Seat=SOLD
          4. Генерируем PDF-билет
          5. Публикуем событие оплаты

        Возвращает: {"payment_id": ..., "ticket_url": ...}
        """
        try:
            order = Order.objects.select_related("seat", "user").get(
                id=order_id, status=OrderStatus.PENDING
            )
        except Order.DoesNotExist:
            raise PaymentError(f"Заказ #{order_id} не найден или уже оплачен")

        # ── Mock Payment Gateway ──────────────────────────────
        # В реальности: response = stripe.PaymentIntent.confirm(card_token)
        payment_id = str(uuid.uuid4())
        logger.info("Mock payment %s for order %s", payment_id, order_id)

        # ── Atomic DB transaction ─────────────────────────────
        with transaction.atomic():
            # 1. Обновляем заказ
            order.status = OrderStatus.PAID
            order.save(update_fields=["status", "updated_at"])

            # 2. Переводим место в SOLD (через SeatService)
            SeatService.mark_seat_sold(
                seat_id=order.seat_id,
                user_id=order.user_id,
            )

        # ── Генерация PDF билета ──────────────────────────────
        ticket_url = TicketService.generate(order=order, payment_id=payment_id)

        # ── Публикация события ────────────────────────────────
        EventService.publish("payment", {
            "type":       "PAYMENT_SUCCESS",
            "order_id":   order_id,
            "payment_id": payment_id,
            "user_id":    order.user_id,
            "amount":     str(order.amount),
        })

        return {
            "payment_id": payment_id,
            "order_id":   order_id,
            "ticket_url": ticket_url,
        }
