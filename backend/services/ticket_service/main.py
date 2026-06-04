import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from common.exception_handlers import setup_exception_handlers
from common.custom_logger import setup_logging
from common.kafka.consumer import KafkaConsumerWrapper
from common.kafka.producer import KafkaProducerWrapper
from common.middleware import CorrelationIdMiddleware
from common.outbox.relay import OutboxRelay
from services.ticket_service.config import settings
from services.ticket_service.database import AsyncSessionLocal
from services.ticket_service.logic.ticket_manager import TicketManager

setup_logging("ticket_service")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Ticket Service Starting...")
    Path(settings.TICKETS_MEDIA_ROOT).mkdir(parents=True, exist_ok=True)

    producer = KafkaProducerWrapper(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    app.state.kafka_producer = producer

    relay = OutboxRelay(session_factory=AsyncSessionLocal, producer=producer)
    relay_task = await relay.start()
    app.state.outbox_relay = relay

    manager = TicketManager()
    consumer = KafkaConsumerWrapper(
        topics=["ticket.commands"],
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="ticket_group",
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
    logger.info("Ticket Service Stopped")


app = FastAPI(title="Ticket Service", lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
setup_exception_handlers(app)

app.mount(
    "/tickets",
    StaticFiles(directory=settings.TICKETS_MEDIA_ROOT),
    name="tickets",
)


@app.get("/health")
async def health():
    return {"status": "ok"}
