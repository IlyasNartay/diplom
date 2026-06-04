from common.database import create_session_factory, get_session_dependency
from services.catalog_service.config import settings

AsyncSessionLocal = create_session_factory(settings.DATABASE_URL)


async def get_db():
    async for session in get_session_dependency(AsyncSessionLocal):
        yield session
