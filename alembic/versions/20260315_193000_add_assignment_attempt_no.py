"""add assignment attempt number

Revision ID: 20260315_193000
Revises: 20260315_180000
Create Date: 2026-03-15 19:30:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision = "20260315_193000"
down_revision = "20260315_180000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "assignments",
        sa.Column(
            "attempt_no",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )


def downgrade() -> None:
    op.drop_column("assignments", "attempt_no")
