"""add answer time_spent_ms

Revision ID: 20260315_180000
Revises: 20260314_120000
Create Date: 2026-03-15 18:00:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision = "20260315_180000"
down_revision = "20260314_120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "answers",
        sa.Column("time_spent_ms", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("answers", "time_spent_ms")
