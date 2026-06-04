import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from common.exception_handlers import setup_exception_handlers
from common.custom_logger import setup_logging
from common.kafka.consumer import KafkaConsumerWrapper
from common.kafka.producer import KafkaProducerWrapper
from common.middleware import CorrelationIdMiddleware
from common.outbox.relay import OutboxRelay
from services.payment_service.api.routes import router as cards_router
from services.payment_service.config import settings
from services.payment_service.database import AsyncSessionLocal
from services.payment_service.logic.payment_manager import PaymentManager

setup_logging("payment_service")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Payment Service Starting...")

    producer = KafkaProducerWrapper(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    app.state.kafka_producer = producer

    relay = OutboxRelay(session_factory=AsyncSessionLocal, producer=producer)
    relay_task = await relay.start()
    app.state.outbox_relay = relay

    manager = PaymentManager()
    consumer = KafkaConsumerWrapper(
        topics=["payment.commands"],
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="payment_group",
        handler=manager.process_kafka_message,
    )
    app.state.kafka_consumer = consumer
    task = asyncio.create_task(consumer.start_consuming())
    app.state.kafka_consumer_task = task

    yield

    await consumer.stop()
    task.cancel()
    await relay.stop()
    await producer.stop()
    logger.info("Payment Service Stopped")


app = FastAPI(title="Payment Service", lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
setup_exception_handlers(app)
app.include_router(cards_router, prefix="/api", tags=["Cards"])


@app.get("/health")
async def health():
    return {"status": "ok"}
