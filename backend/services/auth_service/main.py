import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.exception_handlers import setup_exception_handlers
from common.custom_logger import setup_logging
from common.middleware import CorrelationIdMiddleware
from services.auth_service.api.routes import router

setup_logging("auth_service")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Auth Service Starting...")
    yield
    logger.info("Auth Service Stopped")


app = FastAPI(
    title="Auth Service",
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
app.include_router(router, prefix="/api/auth", tags=["Authentication"])
setup_exception_handlers(app)


@app.get("/health")
async def health():
    return {"status": "ok"}
