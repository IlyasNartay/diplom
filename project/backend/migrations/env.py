from __future__ import annotations

import asyncio
from logging.config import fileConfig
from pathlib import Path
from typing import Any, Final, Optional

from alembic import context
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, async_engine_from_config

from common.database import Base

# IMPORTANT: import ALL models so Alembic can discover metadata.
from services.auth_service.models import *  # noqa: F403
from services.catalog_service.models import *  # noqa: F403
from services.seat_service.models import *  # noqa: F403
from services.orchestrator.models import *  # noqa: F403
from services.order_service.models import *  # noqa: F403
from services.payment_service.models import *  # noqa: F403
from services.ticket_service.models import *  # noqa: F403
from services.analytics_service.models import *  # noqa: F403

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


class _AlembicSettings(BaseSettings):
    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[1] / ".env"),
        extra="ignore",
    )


def _get_database_url() -> str:
    # Prefer env var; otherwise fall back to .env (root) via pydantic-settings.
    url_from_env: Optional[str] = config.get_main_option("sqlalchemy.url")
    if url_from_env:
        return url_from_env

    return _AlembicSettings().DATABASE_URL


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = _get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using AsyncEngine."""
    database_url: Final[str] = _get_database_url()

    ini_section = config.get_section(config.config_ini_section) or {}
    ini_section["sqlalchemy.url"] = database_url

    connectable: AsyncEngine = async_engine_from_config(
        ini_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run() -> None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_migrations_online())


run()
