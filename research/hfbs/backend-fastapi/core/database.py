"""
core/database.py — Async SQLAlchemy + asyncpg
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
КЛЮЧЕВОЕ ОТЛИЧИЕ от Django:
  - Используем AsyncSession вместо обычной Session
  - Все запросы к БД не блокируют event loop
  - FastAPI обрабатывает тысячи запросов в одном потоке (event-loop)
  - Django использует пул потоков + sync psycopg2

Для диплома: именно здесь видно async-преимущество FastAPI.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from core.config import settings

# Создаём async engine (asyncpg — нативный async-драйвер для PostgreSQL)
engine = create_async_engine(
    settings.database_url,
    pool_size=20,           # Размер пула соединений
    max_overflow=10,        # Дополнительные соединения при пиковой нагрузке
    pool_pre_ping=True,     # Проверяем соединение перед использованием
    echo=False,             # True для отладки SQL
)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Объекты доступны после commit
)


class Base(DeclarativeBase):
    pass


# Dependency Injection для FastAPI
async def get_db() -> AsyncSession:
    """
    Используется как: db: AsyncSession = Depends(get_db)
    Гарантирует закрытие сессии после обработки запроса.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
