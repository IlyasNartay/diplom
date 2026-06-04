import asyncio
import logging
from dataclasses import dataclass
from typing import Final, Optional

from aiokafka import AIOKafkaProducer

from common.custom_logger import get_correlation_id

logger: Final = logging.getLogger(__name__)


@dataclass(slots=True)
class KafkaProducerWrapper:
    bootstrap_servers: str
    retry_delay_s: float = 5.0
    _producer: Optional[AIOKafkaProducer] = None

    async def start(self) -> None:
        while True:
            try:
                producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)
                await producer.start()
                self._producer = producer
                logger.info("Kafka producer started")
                return
            except Exception as e:
                logger.error("Kafka producer connection failed: %s. Retry in %ss...", e, self.retry_delay_s)
                await asyncio.sleep(self.retry_delay_s)

    async def send_event(
        self,
        topic: str,
        value: bytes,
        headers: Optional[list[tuple[str, bytes]]] = None,
    ) -> None:
        if self._producer is None:
            raise RuntimeError("KafkaProducerWrapper is not started. Call start() first.")

        if headers is None:
            headers = []
            corr_id = get_correlation_id()
            if corr_id:
                headers.append(("X-Request-ID", corr_id.encode("utf-8")))

        await self._producer.send_and_wait(topic, value, headers=headers)

    async def stop(self) -> None:
        if self._producer is None:
            return
        await self._producer.stop()
        self._producer = None
        logger.info("Kafka producer stopped")
