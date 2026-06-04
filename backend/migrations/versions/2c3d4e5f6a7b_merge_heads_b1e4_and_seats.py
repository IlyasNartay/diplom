"""Merge heads b1e4c9d8a2f7 and 1b2c3d4e5f6a.

Revision ID: 2c3d4e5f6a7b
Revises: b1e4c9d8a2f7, 1b2c3d4e5f6a
Create Date: 2026-03-25
"""


# revision identifiers, used by Alembic.
revision = "2c3d4e5f6a7b"
down_revision = ("b1e4c9d8a2f7", "1b2c3d4e5f6a")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This revision only merges two heads; no schema changes.
    pass


def downgrade() -> None:
    # No-op: merge revision.
    pass
