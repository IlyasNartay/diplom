"""
services/event_service.py — Async EventService (FastAPI)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Асинхронный Kafka producer на основе aiokafka.

СРАВНЕНИЕ (для диплома):
  Django: kafka-python (sync) → вызов producer.send().flush() блокирует поток
  FastAPI: aiokafka (async)   → await producer.send() не блокирует event loop

Оба публикуют события в одни и те же топики Kafka:
  seat.events / order.events / payment.events / ticket.events
"""
import json
import logging
from datetime import datetime

from core.config import settings

logger = logging.getLogger(__name__)

_producer = None  # AIOKafkaProducer — создаётся при старте


async def init_kafka_producer():
    """Вызывается при старте FastAPI (lifespan)."""
    global _producer
    try:
        from aiokafka import AIOKafkaProducer
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all",
            request_timeout_ms=5000,
        )
        await _producer.start()
        logger.info("Async Kafka producer started")
    except Exception as e:
        logger.warning("Kafka unavailable (%s) — mock mode", e)
        _producer = None


async def stop_kafka_producer():
    """Вызывается при остановке FastAPI."""
    if _producer:
        await _producer.stop()


class AsyncEventService:

    @staticmethod
    async def publish(domain: str, payload: dict) -> None:
        """
        Асинхронная публикация события в Kafka.
        await — не блокирует обработку других запросов.
        """
        topic = f"{domain}.events"
        event = {
            **payload,
            "timestamp": datetime.utcnow().isoformat(),
            "source":    "fastapi",
        }

        if _producer:
            try:
                await _producer.send(topic, value=event)
                logger.debug("Async event → %s: %s", topic, event)
            except Exception as e:
                logger.error("Kafka publish error: %s", e)
                AsyncEventService._mock(topic, event)
        else:
            AsyncEventService._mock(topic, event)

    @staticmethod
    def _mock(topic: str, event: dict):
        logger.info("[ASYNC MOCK EVENT] topic=%s | %s", topic, json.dumps(event, ensure_ascii=False))
