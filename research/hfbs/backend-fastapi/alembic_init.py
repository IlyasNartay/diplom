"""
alembic_init.py — Скрипт создания таблиц для FastAPI
(FastAPI использует SQLAlchemy напрямую, без миграций Django)

Запуск:
  docker exec hfbs_fastapi python alembic_init.py
"""
import asyncio
from core.database import engine, Base
from models.db_models import Event, Seat, Order, User  # noqa: импортируем для регистрации


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ FastAPI tables created successfully")


if __name__ == "__main__":
    asyncio.run(create_tables())
