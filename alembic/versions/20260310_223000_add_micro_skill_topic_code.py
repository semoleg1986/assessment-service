"""add micro-skill topic_code

Revision ID: 20260310_223000
Revises: 20260310_210000
Create Date: 2026-03-10 22:30:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision = "20260310_223000"
down_revision = "20260310_210000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "micro_skill_nodes",
        sa.Column("topic_code", sa.String(length=128), nullable=True),
    )
    op.create_foreign_key(
        "fk_micro_skill_nodes_topic_code_topics",
        "micro_skill_nodes",
        "topics",
        ["topic_code"],
        ["code"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_micro_skill_nodes_topic_code_topics",
        "micro_skill_nodes",
        type_="foreignkey",
    )
    op.drop_column("micro_skill_nodes", "topic_code")
