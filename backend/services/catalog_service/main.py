import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from common.exception_handlers import setup_exception_handlers
from common.custom_logger import setup_logging
from common.middleware import CorrelationIdMiddleware
from services.catalog_service.api.routes import router
from services.catalog_service.config import settings
from services.catalog_service.logic.poster_storage import ensure_media_dirs

setup_logging("catalog_service")
logger = logging.getLogger(__name__)

tags_metadata = [{"name": "Events"}, {"name": "Cities"}, {"name": "Categories"}, {"name": "Admin"}]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Catalog Service Starting...")
    Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
    ensure_media_dirs()
    yield
    logger.info("Catalog Service Stopped")


app = FastAPI(
    title="Catalog Service",
    version="1.0.0",
    openapi_tags=tags_metadata,
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
app.mount("/media", StaticFiles(directory=settings.MEDIA_ROOT), name="media")
setup_exception_handlers(app)


@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok"}
