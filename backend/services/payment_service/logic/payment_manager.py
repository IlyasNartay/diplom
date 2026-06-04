import asyncio
import json
import logging
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.commands import CreatePaymentCommand
from common.custom_logger import get_correlation_id
from common.events import PaymentFailedEvent, PaymentSucceededEvent
from common.outbox.models import OutboxEvent
from services.payment_service.database import AsyncSessionLocal
from services.payment_service.models import Payment

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


class PaymentManager:
    async def process_kafka_message(self, msg_value: bytes):
        try:
            data = json.loads(msg_value.decode("utf-8"))
            if data.get("type") != "CreatePayment":
                return

            command = CreatePaymentCommand(**data)
            logger.info(f"Received payment request for order {command.order_id}")

            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Payment).where(Payment.booking_id == command.booking_id))
                existing_payment = result.scalar_one_or_none()

                if existing_payment:
                    logger.warning(
                        f"Idempotency: Payment for booking {command.booking_id} already exists "
                        f"(status={existing_payment.status}). Re-emitting event."
                    )
                    event = self._build_event_for_existing(existing_payment, command)
                    _enqueue_event(db, "payment.events", event.model_dump_json().encode("utf-8"))
                    await db.commit()
                    return

                payment = Payment(
                    booking_id=command.booking_id,
                    order_id=command.order_id,
                    user_id=command.user_id,
                    amount=command.amount,
                    status="PENDING",
                )
                db.add(payment)
                await db.flush()

                logger.info("Waiting for Bank Gateway...")
                await asyncio.sleep(3)

                is_success = random.random() < 0.9
                if is_success:
                    payment.status = "SUCCESS"
                    event = PaymentSucceededEvent(
                        booking_id=command.booking_id, order_id=command.order_id, payment_id=payment.id
                    )
                    logger.info(f"Payment {payment.id} SUCCESSFUL!")
                else:
                    payment.status = "FAILED"
                    payment.error_reason = "INSUFFICIENT_FUNDS"
                    event = PaymentFailedEvent(
                        booking_id=command.booking_id, order_id=command.order_id, reason="INSUFFICIENT_FUNDS"
                    )
                    logger.info(f"Payment {payment.id} DECLINED by bank!")

                _enqueue_event(db, "payment.events", event.model_dump_json().encode("utf-8"))
                await db.commit()

        except Exception as e:
            logger.error(f"Error in PaymentManager: {e}")

    @staticmethod
    def _build_event_for_existing(payment: Payment, command: CreatePaymentCommand):
        if payment.status == "SUCCESS":
            return PaymentSucceededEvent(
                booking_id=command.booking_id, order_id=command.order_id, payment_id=payment.id
            )
        if payment.status == "FAILED":
            return PaymentFailedEvent(
                booking_id=command.booking_id,
                order_id=command.order_id,
                reason=payment.error_reason or "UNKNOWN",
            )
        return PaymentFailedEvent(
            booking_id=command.booking_id,
            order_id=command.order_id,
            reason="PAYMENT_STILL_PENDING",
        )
