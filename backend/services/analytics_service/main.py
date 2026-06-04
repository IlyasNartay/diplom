import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from common.exception_handlers import setup_exception_handlers
from common.custom_logger import setup_logging
from common.kafka.consumer import KafkaConsumerWrapper
from common.middleware import CorrelationIdMiddleware
from services.analytics_service.config import settings
from services.analytics_service.kafka_consumer import analytics_handler

setup_logging("analytics_service")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Analytics Service Starting...")

    consumer = KafkaConsumerWrapper(
        topics=["seat.events", "order.events", "payment.events", "ticket.events"],
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="analytics_group",
        handler=analytics_handler,
    )
    app.state.kafka_consumer = consumer
    task = asyncio.create_task(consumer.start_consuming())
    app.state.kafka_consumer_task = task

    yield

    await consumer.stop()
    task.cancel()
    logger.info("Analytics Service Stopped")


app = FastAPI(title="Analytics Service", lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
setup_exception_handlers(app)


@app.get("/health")
async def health():
    return {"status": "ok"}
