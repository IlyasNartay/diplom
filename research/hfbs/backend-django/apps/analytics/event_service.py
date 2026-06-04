"""
apps/analytics/event_service.py — EventService
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Event-driven архитектура: все сервисы публикуют события через EventService.

Топики Kafka:
  seat.events     → SeatEvt
  order.events    → OrderEvt
  payment.events  → PaymentEvt
  ticket.events   → TicketEvt

Потребитель этих событий — Analytics DB (отдельный сервис).

Fallback: если Kafka недоступна → события логируются (mock-режим).
Это позволяет запускать проект без Kafka для разработки.
"""
import json
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)

_producer = None  # Kafka producer — ленивая инициализация


def _get_producer():
    """Создаём Kafka producer при первом вызове (lazy init)."""
    global _producer
    if _producer is not None:
        return _producer

    try:
        from kafka import KafkaProducer
        _producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all",          # Ждём подтверждения от всех реплик
            retries=3,
            request_timeout_ms=5000,
        )
        logger.info("Kafka producer connected to %s", settings.KAFKA_BOOTSTRAP_SERVERS)
    except Exception as e:
        logger.warning("Kafka unavailable (%s) — using mock EventService", e)
        _producer = None

    return _producer


class EventService:
    """
    Публикует доменные события в Kafka.
    Используется всеми сервисами: Seat, Order, Payment, Ticket.
    """

    @staticmethod
    def publish(domain: str, payload: dict) -> None:
        """
        :param domain:  'seat' | 'order' | 'payment' | 'ticket'
        :param payload: словарь с данными события
        """
        topic = settings.KAFKA_TOPICS.get(domain, f"{domain}.events")

        # Добавляем метаданные
        event = {
            **payload,
            "timestamp": datetime.utcnow().isoformat(),
            "source":    "django",
        }

        producer = _get_producer()
        if producer:
            try:
                producer.send(topic, value=event)
                producer.flush(timeout=2)
                logger.debug("Event published to %s: %s", topic, event)
            except Exception as e:
                logger.error("Failed to publish event to Kafka: %s", e)
                # Fallback: запись в лог (в продакшне можно писать в БД)
                EventService._mock_publish(topic, event)
        else:
            EventService._mock_publish(topic, event)

    @staticmethod
    def _mock_publish(topic: str, event: dict) -> None:
        """Mock-режим: просто логируем событие."""
        logger.info("[MOCK EVENT] topic=%s | %s", topic, json.dumps(event, ensure_ascii=False))
