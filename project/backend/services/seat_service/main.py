import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis import asyncio as aioredis

from common.exception_handlers import setup_exception_handlers
from common.custom_logger import setup_logging
from common.middleware import CorrelationIdMiddleware
from common.kafka.producer import KafkaProducerWrapper
from common.outbox.relay import OutboxRelay
from services.seat_service.api.routes import router
from services.seat_service.config import settings
from services.seat_service.database import AsyncSessionLocal
from services.seat_service.kafka_consumer import build_seat_consumer

setup_logging("seat_service")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Seat Service Starting...")

    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    app.state.redis = redis

    producer = KafkaProducerWrapper(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    app.state.kafka_producer = producer

    relay = OutboxRelay(session_factory=AsyncSessionLocal, producer=producer)
    relay_task = await relay.start()
    app.state.outbox_relay = relay

    consumer = build_seat_consumer(redis=redis)
    app.state.kafka_consumer = consumer
    consumer_task = asyncio.create_task(consumer.start_consuming())
    app.state.kafka_consumer_task = consumer_task

    yield

    await consumer.stop()
    consumer_task.cancel()
    await relay.stop()
    await producer.stop()
    await redis.close()
    logger.info("Seat Service Stopped")


app = FastAPI(
    title="Seat Service",
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
app.include_router(router, prefix="/api", tags=["Seats"])
setup_exception_handlers(app)
