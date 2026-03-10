"""add micro-skill metadata fields

Revision ID: 20260310_210000
Revises: 20260308_140000
Create Date: 2026-03-10 21:00:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision = "20260310_210000"
down_revision = "20260308_140000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "micro_skill_nodes",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "micro_skill_nodes",
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="active",
        ),
    )
    op.add_column(
        "micro_skill_nodes",
        sa.Column("external_ref", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "micro_skill_nodes",
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column(
        "micro_skill_nodes",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("TIMEZONE('utc', NOW())"),
        ),
    )
    op.add_column(
        "micro_skill_nodes",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("TIMEZONE('utc', NOW())"),
        ),
    )


def downgrade() -> None:
    op.drop_column("micro_skill_nodes", "updated_at")
    op.drop_column("micro_skill_nodes", "created_at")
    op.drop_column("micro_skill_nodes", "version")
    op.drop_column("micro_skill_nodes", "external_ref")
    op.drop_column("micro_skill_nodes", "status")
    op.drop_column("micro_skill_nodes", "description")
