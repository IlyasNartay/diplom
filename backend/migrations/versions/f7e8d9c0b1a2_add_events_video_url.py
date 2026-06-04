"""Add optional video_url (trailer) to events.

Revision ID: f7e8d9c0b1a2
Revises: 2c3d4e5f6a7b
Create Date: 2026-04-04
"""

import sqlalchemy as sa
from alembic import op

revision = "f7e8d9c0b1a2"
down_revision = "2c3d4e5f6a7b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("events", sa.Column("video_url", sa.String(length=1000), nullable=True))


def downgrade() -> None:
    op.drop_column("events", "video_url")
