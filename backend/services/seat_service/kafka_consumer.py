import logging
from typing import Final

from redis.asyncio import Redis

from common.kafka.consumer import KafkaConsumerWrapper
from services.seat_service.config import settings
from services.seat_service.logic.seat_manager import SeatManager

logger: Final = logging.getLogger(__name__)


def build_seat_consumer(*, redis: Redis) -> KafkaConsumerWrapper:
    manager = SeatManager(redis)
    return KafkaConsumerWrapper(
        topics=["seat.commands"],
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="seat_group",
        handler=manager.process_kafka_message,
    )
