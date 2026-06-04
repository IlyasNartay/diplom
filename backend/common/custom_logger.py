import logging
import sys
import uuid
from typing import Optional

from contextvars import ContextVar

# Контекстная переменная для хранения Correlation ID
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)

class CorrelationFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = correlation_id_ctx.get() or "N/A"
        return True

def setup_logging(service_name: str):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Удаляем существующие хендлеры, чтобы не было дублей
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        f"[%(asctime)s] [%(levelname)s] [{service_name}] [ReqID: %(correlation_id)s] %(message)s"
    )
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationFilter())
    logger.addHandler(handler)

    # Перенаправляем стандартный print в логгер для удобства (опционально, но полезно)
    # Но лучше приучить проект к использованию logging.info()

def get_correlation_id() -> Optional[str]:
    return correlation_id_ctx.get()

def set_correlation_id(id_str: str):
    correlation_id_ctx.set(id_str)

def generate_correlation_id() -> str:
    return str(uuid.uuid4())
