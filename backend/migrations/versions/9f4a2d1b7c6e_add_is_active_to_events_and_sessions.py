"""add is_active to events and sessions

Revision ID: 9f4a2d1b7c6e
Revises: e7b1a9c2d4f3
Create Date: 2026-03-24 10:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9f4a2d1b7c6e"
down_revision = "e7b1a9c2d4f3"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {c["name"] for c in inspector.get_columns(table_name)}


def upgrade() -> None:
    if "is_active" not in _column_names("events"):
        op.add_column(
            "events",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        )
    if "is_active" not in _column_names("sessions"):
        op.add_column(
            "sessions",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        )


def downgrade() -> None:
    if "is_active" in _column_names("sessions"):
        op.drop_column("sessions", "is_active")
    if "is_active" in _column_names("events"):
        op.drop_column("events", "is_active")
