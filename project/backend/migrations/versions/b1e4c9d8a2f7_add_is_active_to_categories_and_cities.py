"""add is_active to categories and cities

Revision ID: b1e4c9d8a2f7
Revises: 9f4a2d1b7c6e
Create Date: 2026-03-24 10:30:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b1e4c9d8a2f7"
down_revision = "9f4a2d1b7c6e"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {c["name"] for c in inspector.get_columns(table_name)}


def upgrade() -> None:
    if "is_active" not in _column_names("categories"):
        op.add_column(
            "categories",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        )
    if "is_active" not in _column_names("cities"):
        op.add_column(
            "cities",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        )


def downgrade() -> None:
    if "is_active" in _column_names("cities"):
        op.drop_column("cities", "is_active")
    if "is_active" in _column_names("categories"):
        op.drop_column("categories", "is_active")
