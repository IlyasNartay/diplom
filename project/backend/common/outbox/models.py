from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base


class OutboxEvent(Base):
    """
    Transactional Outbox table.

    Each service that uses the outbox pattern should import this model
    so that Alembic / create_all picks up the table.
    """

    __tablename__ = "outbox_events"

    topic: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    payload: Mapped[str] = mapped_column(sa.Text, nullable=False)
    headers: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa.text("'{}'::jsonb"))
    processed: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False, server_default=sa.text("false")
    )
