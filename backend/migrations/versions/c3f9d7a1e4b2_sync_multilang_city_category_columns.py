"""sync multilingual city/category columns

Revision ID: c3f9d7a1e4b2
Revises: 8ca5a3b4a219
Create Date: 2026-03-23 12:20:00.000000
"""
from __future__ import annotations

from typing import Iterable

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c3f9d7a1e4b2"
down_revision = "8ca5a3b4a219"
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


def _index_exists(index_name: str) -> bool:
    bind = op.get_bind()
    row = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM pg_indexes
            WHERE indexname = :name
            LIMIT 1
            """
        ),
        {"name": index_name},
    ).first()
    return row is not None


def _ensure_unique_constraints(table_name: str, columns: Iterable[str]) -> None:
    for col in columns:
        constraint_name = f"{table_name}_{col}_key"
        if not _constraint_exists(constraint_name):
            op.create_unique_constraint(constraint_name, table_name, [col])


def _upgrade_multilang_for_table(table_name: str) -> None:
    cols = _column_names(table_name)

    # 1) Add multilingual columns if missing (nullable first for safe backfill).
    for lang_col in ("name_ru", "name_en", "name_kz"):
        if lang_col not in cols:
            op.add_column(table_name, sa.Column(lang_col, sa.String(length=50), nullable=True))

    # 2) Backfill from legacy single-language 'name' if present.
    cols = _column_names(table_name)
    if "name" in cols:
        op.execute(
            sa.text(
                f"""
                UPDATE {table_name}
                SET
                    name_ru = COALESCE(name_ru, name),
                    name_en = COALESCE(name_en, name),
                    name_kz = COALESCE(name_kz, name)
                """
            )
        )

    # 3) Fill any remaining NULLs with deterministic unique placeholders.
    op.execute(
        sa.text(
            f"""
            UPDATE {table_name}
            SET
                name_ru = COALESCE(name_ru, 'auto_ru_' || id::text),
                name_en = COALESCE(name_en, 'auto_en_' || id::text),
                name_kz = COALESCE(name_kz, 'auto_kz_' || id::text)
            """
        )
    )

    # 4) Enforce NOT NULL + UNIQUE for all 3 columns.
    for lang_col in ("name_ru", "name_en", "name_kz"):
        op.alter_column(table_name, lang_col, existing_type=sa.String(length=50), nullable=False)

    _ensure_unique_constraints(table_name, ("name_ru", "name_en", "name_kz"))

    # 5) Remove legacy single-column uniqueness/index if present (optional cleanup).
    legacy_constraint = f"{table_name}_name_key"
    if _constraint_exists(legacy_constraint):
        op.drop_constraint(legacy_constraint, table_name, type_="unique")

    legacy_index = f"ix_{table_name}_name"
    if _index_exists(legacy_index):
        op.drop_index(legacy_index, table_name=table_name)

    # 6) Drop the legacy 'name' column — no longer used by the model.
    cols = _column_names(table_name)
    if "name" in cols:
        op.drop_column(table_name, "name")


def upgrade() -> None:
    _upgrade_multilang_for_table("cities")
    _upgrade_multilang_for_table("categories")


def downgrade() -> None:
    # Keep downgrade conservative: do not drop multilingual columns automatically
    # to avoid data loss on production environments.
    pass
