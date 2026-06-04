import datetime
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.commands import CancelOrderCommand, ReleaseSeatCommand
from common.custom_logger import get_correlation_id
from common.outbox.models import OutboxEvent
from services.orchestrator.database import AsyncSessionLocal
from services.orchestrator.models import BookingSaga, SagaStatus

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


class CleanupService:
    async def clean_zombies(self):
        logger.info("Cleanup: Searching for zombies...")

        async with AsyncSessionLocal() as db:
            ten_minutes_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=10)

            active_statuses = [
                SagaStatus.started,
                SagaStatus.seat_reserved,
                SagaStatus.order_created,
                SagaStatus.payment_pending,
            ]

            query = select(BookingSaga).where(
                BookingSaga.status.in_(active_statuses), BookingSaga.updated_at < ten_minutes_ago
            )

            result = await db.execute(query)
            zombies = result.scalars().all()

            if not zombies:
                logger.info("Cleanup: No zombies found.")
                return

            logger.info(f"Found {len(zombies)} zombies. Killing them...")

            for saga in zombies:
                if saga.status in [
                    SagaStatus.started,
                    SagaStatus.seat_reserved,
                    SagaStatus.order_created,
                    SagaStatus.payment_pending,
                ]:
                    cmd = ReleaseSeatCommand(booking_id=saga.id, seat_ids=saga.seat_ids)
                    _enqueue_event(db, "seat.commands", cmd.model_dump_json().encode("utf-8"))
                    logger.info(f"Sent ReleaseSeat for zombie {saga.id}")

                if saga.status in [SagaStatus.order_created, SagaStatus.payment_pending]:
                    cmd_order = CancelOrderCommand(booking_id=saga.id, reason="Timeout / Zombie Cleanup")
                    _enqueue_event(db, "order.commands", cmd_order.model_dump_json().encode("utf-8"))
                    logger.info(f"Sent CancelOrder for zombie {saga.id}")

                saga.status = SagaStatus.cancelled
                saga.error_reason = "Transaction timed out (Zombie Cleanup)"

            await db.commit()
