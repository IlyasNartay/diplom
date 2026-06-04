"""Link seats to sessions (session_id instead of event_id).

Revision ID: 1b2c3d4e5f6a
Revises: e7b1a9c2d4f3
Create Date: 2026-03-25
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1b2c3d4e5f6a"
down_revision = "e7b1a9c2d4f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("seats", sa.Column("session_id", sa.UUID(), nullable=True))

    # Best-effort backfill:
    # If there are existing seats linked to event_id, bind them to the earliest session of that event.
    # This migration must remain valid before the later branch that introduces sessions.is_active.
    op.execute(sa.text("""
        UPDATE seats s
        SET session_id = sub.session_id
        FROM (
            SELECT DISTINCT ON (sess.event_id) sess.event_id, sess.id AS session_id
            FROM sessions sess
            ORDER BY sess.event_id, sess.start_time ASC
        ) sub
        WHERE s.session_id IS NULL AND s.event_id = sub.event_id
    """))

    # If some events had no sessions, we cannot safely assign; keep nullable in that case.
    # Enforce non-null only when fully backfilled.
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM seats WHERE session_id IS NULL) THEN
                ALTER TABLE seats ALTER COLUMN session_id SET NOT NULL;
            END IF;
        END $$;
    """))

    # Swap index to session_id
    op.drop_index("ix_seats_event_id", table_name="seats")
    op.create_index(op.f("ix_seats_session_id"), "seats", ["session_id"], unique=False)

    # Optional: prevent duplicates within a session (row/number)
    op.create_unique_constraint("uq_seats_session_row_number", "seats", ["session_id", "row", "number"])

    # Drop old column only if everything is backfilled
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM seats WHERE session_id IS NULL) THEN
                ALTER TABLE seats DROP COLUMN event_id;
            END IF;
        END $$;
    """))


def downgrade() -> None:
    # Downgrade cannot reliably restore event_id for all rows; perform best-effort.
    op.add_column("seats", sa.Column("event_id", sa.UUID(), nullable=True))

    op.execute(sa.text("""
        UPDATE seats s
        SET event_id = sess.event_id
        FROM sessions sess
        WHERE s.session_id = sess.id AND s.event_id IS NULL
    """))

    op.drop_constraint("uq_seats_session_row_number", "seats", type_="unique")
    op.drop_index(op.f("ix_seats_session_id"), table_name="seats")
    op.create_index("ix_seats_event_id", "seats", ["event_id"], unique=False)
    op.drop_column("seats", "session_id")
