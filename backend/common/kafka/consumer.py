import asyncio
import logging
from dataclasses import dataclass
import inspect
from typing import Awaitable, Callable, Final, Optional, Protocol, Union

from aiokafka import AIOKafkaConsumer

from common.custom_logger import set_correlation_id

logger: Final = logging.getLogger(__name__)

class BytesHandler(Protocol):
    def __call__(self, value: bytes) -> Awaitable[None]: ...


class TopicBytesHandler(Protocol):
    def __call__(self, topic: str, value: bytes) -> Awaitable[None]: ...


KafkaHandler = Union[BytesHandler, TopicBytesHandler]


@dataclass(slots=True)
class KafkaConsumerWrapper:
    topics: list[str]
    bootstrap_servers: str
    group_id: str
    handler: KafkaHandler
    retry_delay_s: float = 5.0

    _consumer: Optional[AIOKafkaConsumer] = None
    _stopping: bool = False

    async def start_consuming(self) -> None:
        self._stopping = False

        while not self._stopping:
            try:
                consumer = AIOKafkaConsumer(
                    *self.topics,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=self.group_id,
                )
                self._consumer = consumer
                await consumer.start()
                logger.info("Kafka consumer started for topics=%s group_id=%s", self.topics, self.group_id)

                try:
                    async for msg in consumer:
                        if self._stopping:
                            break

                        corr_id: Optional[str] = None
                        if msg.headers:
                            for key, value in msg.headers:
                                if key == "X-Request-ID" and value is not None:
                                    corr_id = value.decode("utf-8")
                                    break

                        # пустая строка => CorrelationFilter покажет "N/A"
                        set_correlation_id(corr_id or "")

                        try:
                            if _expects_topic(self.handler):
                                await self.handler(msg.topic, msg.value)  # type: ignore[misc]
                            else:
                                await self.handler(msg.value)  # type: ignore[misc]
                        except Exception as e:
                            logger.error("Poison pill handled (continuing). Error=%s", e, exc_info=True)
                finally:
                    await consumer.stop()
                    self._consumer = None

            except Exception as e:
                if self._stopping:
                    break
                logger.error("Kafka consumer error: %s. Retry in %ss...", e, self.retry_delay_s, exc_info=True)
                await asyncio.sleep(self.retry_delay_s)

    async def stop(self) -> None:
        self._stopping = True
        if self._consumer is not None:
            await self._consumer.stop()
            self._consumer = None
        logger.info("Kafka consumer stopped")


def _expects_topic(handler: KafkaHandler) -> bool:
    """
    Supports two handler styles:
    - handler(value: bytes)
    - handler(topic: str, value: bytes)
    """
    try:
        return len(inspect.signature(handler).parameters) >= 2
    except (TypeError, ValueError):
        return False
