import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.exception_handlers import setup_exception_handlers
from common.custom_logger import setup_logging
from common.kafka.consumer import KafkaConsumerWrapper
from common.kafka.producer import KafkaProducerWrapper
from common.middleware import CorrelationIdMiddleware
from common.outbox.relay import OutboxRelay
from services.orchestrator.api.routes import router
from services.orchestrator.config import settings
from services.orchestrator.database import AsyncSessionLocal
from services.orchestrator.logic.cleanup_service import CleanupService
from services.orchestrator.logic.saga_manager import SagaManager

setup_logging("orchestrator")
logger = logging.getLogger(__name__)


async def cleanup_loop():
    service = CleanupService()
    while True:
        try:
            await service.clean_zombies()
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Orchestrator Starting...")

    producer = KafkaProducerWrapper(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    app.state.kafka_producer = producer

    app.state.saga_manager = SagaManager()
    logger.info("Kafka Producer & SagaManager Ready")

    relay = OutboxRelay(session_factory=AsyncSessionLocal, producer=producer)
    relay_task = await relay.start()
    app.state.outbox_relay = relay

    consumer = KafkaConsumerWrapper(
        topics=["seat.events", "order.events", "payment.events", "ticket.events"],
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="orchestrator_group",
        handler=app.state.saga_manager.process_kafka_event,
    )
    app.state.kafka_consumer = consumer
    task = asyncio.create_task(consumer.start_consuming())
    app.state.kafka_consumer_task = task
    cleanup_task = asyncio.create_task(cleanup_loop())

    yield

    await consumer.stop()
    task.cancel()
    await relay.stop()
    await producer.stop()
    cleanup_task.cancel()
    logger.info("Orchestrator Stopped")


app = FastAPI(
    title="Orchestrator",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")
setup_exception_handlers(app)
