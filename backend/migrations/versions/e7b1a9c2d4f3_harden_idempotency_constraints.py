"""harden idempotency constraints

Revision ID: e7b1a9c2d4f3
Revises: c3f9d7a1e4b2
Create Date: 2026-03-23 12:45:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e7b1a9c2d4f3"
down_revision = "c3f9d7a1e4b2"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {c["name"] for c in inspector.get_columns(table_name)}


def _constraint_exists(constraint_name: str) -> bool:
    bind = op.get_bind()
    row = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM pg_constraint
            WHERE conname = :name
            LIMIT 1
            """
        ),
        {"name": constraint_name},
    ).first()
    return row is not None


def _ensure_booking_unique(table_name: str) -> None:
    cols = _column_names(table_name)
    if "booking_id" not in cols:
        return

    constraint_name = f"{table_name}_booking_id_key"
    if not _constraint_exists(constraint_name):
        op.create_unique_constraint(constraint_name, table_name, ["booking_id"])


def upgrade() -> None:
    # Ensure constraints required by idempotent command handlers.
    _ensure_booking_unique("orders")
    _ensure_booking_unique("payments")
    _ensure_booking_unique("tickets")

    # payments.booking_id must be NOT NULL for strong idempotency guarantees.
    if "booking_id" in _column_names("payments"):
        null_count = op.get_bind().execute(
            sa.text("SELECT COUNT(*) FROM payments WHERE booking_id IS NULL")
        ).scalar_one()
        if null_count and int(null_count) > 0:
            raise RuntimeError(
                "Cannot enforce payments.booking_id NOT NULL: found existing NULL rows. "
                "Please backfill those rows manually first."
            )
        op.alter_column("payments", "booking_id", existing_type=sa.UUID(), nullable=False)


def downgrade() -> None:
    # Intentionally conservative: keep stricter constraints in place.
    pass
