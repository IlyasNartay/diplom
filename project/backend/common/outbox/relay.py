from __future__ import annotations

import asyncio
import logging
from typing import Final, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from common.kafka.producer import KafkaProducerWrapper
from common.outbox.models import OutboxEvent

logger: Final = logging.getLogger(__name__)


class OutboxRelay:
    """
    Background worker that polls the outbox_events table and publishes
    pending messages to Kafka, then marks them as processed.

    Uses SELECT … FOR UPDATE SKIP LOCKED to allow safe concurrent workers.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        producer: KafkaProducerWrapper,
        poll_interval_s: float = 0.5,
        batch_size: int = 50,
    ) -> None:
        self._session_factory = session_factory
        self._producer = producer
        self._poll_interval_s = poll_interval_s
        self._batch_size = batch_size
        self._stopping = False
        self._task: Optional[asyncio.Task[None]] = None

    async def start(self) -> asyncio.Task[None]:
        self._stopping = False
        self._task = asyncio.create_task(self._loop())
        logger.info("OutboxRelay started (poll=%.2fs, batch=%d)", self._poll_interval_s, self._batch_size)
        return self._task

    async def stop(self) -> None:
        self._stopping = True
        if self._task is not None:
            self._task.cancel()
            self._task = None
        logger.info("OutboxRelay stopped")

    async def _loop(self) -> None:
        while not self._stopping:
            try:
                await self._poll_and_publish()
            except Exception as e:
                logger.error("OutboxRelay error: %s", e, exc_info=True)
            await asyncio.sleep(self._poll_interval_s)

    async def _poll_and_publish(self) -> None:
        async with self._session_factory() as db:
            stmt = (
                select(OutboxEvent)
                .where(OutboxEvent.processed == False)  # noqa: E712
                .order_by(OutboxEvent.created_at.asc())
                .limit(self._batch_size)
                .with_for_update(skip_locked=True)
            )
            result = await db.execute(stmt)
            events = result.scalars().all()

            if not events:
                return

            published_ids: list = []

            for evt in events:
                kafka_headers: list[tuple[str, bytes]] = []
                if isinstance(evt.headers, dict):
                    for k, v in evt.headers.items():
                        kafka_headers.append((k, v.encode("utf-8") if isinstance(v, str) else v))

                try:
                    await self._producer.send_event(
                        topic=evt.topic,
                        value=evt.payload.encode("utf-8"),
                        headers=kafka_headers,
                    )
                    published_ids.append(evt.id)
                except Exception as e:
                    logger.error("Failed to publish outbox event %s: %s", evt.id, e, exc_info=True)
                    break

            if published_ids:
                await db.execute(
                    update(OutboxEvent)
                    .where(OutboxEvent.id.in_(published_ids))
                    .values(processed=True)
                )
                await db.commit()
                logger.info("OutboxRelay published %d events", len(published_ids))
