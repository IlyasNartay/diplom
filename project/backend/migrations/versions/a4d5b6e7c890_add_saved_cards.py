"""Add saved_cards table.

Revision ID: a4d5b6e7c890
Revises: f7e8d9c0b1a2
Create Date: 2026-04-26
"""

import sqlalchemy as sa
from alembic import op

revision = "a4d5b6e7c890"
down_revision = "f7e8d9c0b1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_cards",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("brand", sa.String(length=20), nullable=False),
        sa.Column("last4", sa.String(length=4), nullable=False),
        sa.Column("pan_full", sa.String(length=19), nullable=False),
        sa.Column("exp_month", sa.Integer(), nullable=False),
        sa.Column("exp_year", sa.Integer(), nullable=False),
        sa.Column("cvv", sa.String(length=4), nullable=False),
        sa.Column("holder_name", sa.String(length=120), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_saved_cards_user_id"), "saved_cards", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_saved_cards_user_id"), table_name="saved_cards")
    op.drop_table("saved_cards")
