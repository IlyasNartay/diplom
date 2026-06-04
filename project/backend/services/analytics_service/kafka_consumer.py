import json
import logging
import uuid
from typing import Final

from common.custom_logger import get_correlation_id
from services.analytics_service.database import AsyncSessionLocal
from services.analytics_service.models import AuditLog

logger: Final = logging.getLogger(__name__)


async def analytics_handler(topic: str, msg_value: bytes) -> None:
    try:
        payload = json.loads(msg_value.decode("utf-8"))
        event_type = payload.get("type", "UNKNOWN")
        booking_id_str = payload.get("booking_id")
        booking_uuid = uuid.UUID(booking_id_str) if booking_id_str else None

        logger.info("Logging %s from %s", event_type, topic)

        async with AsyncSessionLocal() as db:
            log_entry = AuditLog(
                topic=topic,
                event_type=event_type,
                booking_id=booking_uuid,
                correlation_id=get_correlation_id(),
                payload=payload,
            )
            db.add(log_entry)
            await db.commit()
    except Exception as e:
        logger.error("Error saving analytics: %s", e, exc_info=True)
