import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.commands import CancelOrderCommand, CompleteOrderCommand, CreateOrderCommand
from common.custom_logger import get_correlation_id
from common.events import OrderCancelledEvent, OrderCompletedEvent, OrderCreatedEvent
from common.outbox.models import OutboxEvent
from services.order_service.database import AsyncSessionLocal
from services.order_service.models import Order

logger = logging.getLogger(__name__)


def _outbox_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    corr_id = get_correlation_id()
    if corr_id:
        headers["X-Request-ID"] = corr_id
    return headers


def _enqueue_event(db: AsyncSession, topic: str, payload_bytes: bytes) -> None:
    db.add(OutboxEvent(
        topic=topic,
        payload=payload_bytes.decode("utf-8"),
        headers=_outbox_headers(),
    ))


class OrderManager:
    async def process_kafka_message(self, msg_value: bytes):
        try:
            data = json.loads(msg_value.decode("utf-8"))
            msg_type = data.get("type")

            if msg_type == "CreateOrder":
                command = CreateOrderCommand(**data)
                logger.info(f"Creating order for booking {command.booking_id}")

                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(Order).where(Order.booking_id == command.booking_id))
                    existing = result.scalar_one_or_none()
                    if existing:
                        logger.warning(f"Idempotency: Order for {command.booking_id} already exists. Re-emitting event.")
                        event = OrderCreatedEvent(
                            booking_id=existing.booking_id, order_id=existing.id,
                            status=existing.status, price=existing.price,
                        )
                        _enqueue_event(db, "order.events", event.model_dump_json().encode("utf-8"))
                        await db.commit()
                        return

                    new_order = Order(
                        booking_id=command.booking_id,
                        user_id=command.user_id,
                        price=command.price,
                        status="PENDING",
                    )
                    db.add(new_order)
                    await db.flush()

                    event = OrderCreatedEvent(
                        booking_id=command.booking_id, order_id=new_order.id, status="PENDING", price=new_order.price
                    )
                    _enqueue_event(db, "order.events", event.model_dump_json().encode("utf-8"))
                    await db.commit()

                    logger.info(f"Order {new_order.id} saved. Sent OrderCreated event for {command.booking_id}")

            elif msg_type == "CompleteOrder":
                cmd = CompleteOrderCommand(**data)
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(Order).where(Order.id == cmd.order_id))
                    order = result.scalar_one_or_none()
                    if order:
                        if order.status == "PAID":
                            logger.info(f"Idempotency: Order {order.id} is already PAID. Re-emitting.")
                            evt = OrderCompletedEvent(booking_id=cmd.booking_id, order_id=cmd.order_id)
                            _enqueue_event(db, "order.events", evt.model_dump_json().encode("utf-8"))
                            await db.commit()
                            return
                        if order.status == "CANCELLED":
                            logger.error(f"CRITICAL: Trying to complete CANCELLED order {order.id}! Ignoring.")
                            return

                        order.status = "PAID"

                        evt = OrderCompletedEvent(booking_id=cmd.booking_id, order_id=cmd.order_id)
                        _enqueue_event(db, "order.events", evt.model_dump_json().encode("utf-8"))
                        await db.commit()
                        logger.info(f"Order {cmd.order_id} marked as PAID!")

            elif msg_type == "CancelOrder":
                cmd = CancelOrderCommand(**data)
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(Order).where(Order.booking_id == cmd.booking_id))
                    order = result.scalar_one_or_none()
                    if order:
                        if order.status == "CANCELLED":
                            logger.info(f"Idempotency: Order {order.id} is already CANCELLED. Re-emitting.")
                            evt = OrderCancelledEvent(booking_id=cmd.booking_id, order_id=order.id, reason=order.error_reason or "Unknown reason")
                            _enqueue_event(db, "order.events", evt.model_dump_json().encode("utf-8"))
                            await db.commit()
                            return
                        if order.status == "PAID":
                            logger.error(f"CRITICAL: Trying to cancel PAID order {order.id}! Needs manual refund.")
                            order.status = "REFUNDED"
                        else:
                            order.status = "CANCELLED"

                        order.error_reason = cmd.reason

                        evt = OrderCancelledEvent(booking_id=cmd.booking_id, order_id=order.id, reason=cmd.reason)
                        _enqueue_event(db, "order.events", evt.model_dump_json().encode("utf-8"))
                        await db.commit()
                        logger.info(f"Order {cmd.booking_id} marked as {order.status} (Rollback)!")

        except Exception as e:
            logger.error(f"Error in OrderManager: {e}")
