"""add question types and diagnostics

Revision ID: 20260314_120000
Revises: 20260310_223000
Create Date: 2026-03-14 12:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision = "20260314_120000"
down_revision = "20260310_223000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column(
            "question_type",
            sa.String(length=32),
            nullable=False,
            server_default="text",
        ),
    )
    op.add_column(
        "questions",
        sa.Column("correct_option_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "questions",
        sa.Column(
            "options",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "questions",
        sa.Column(
            "text_distractors",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.alter_column("questions", "answer_key", existing_type=sa.Text(), nullable=True)

    op.alter_column("answers", "value", existing_type=sa.Text(), nullable=True)
    op.add_column(
        "answers",
        sa.Column("selected_option_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "answers",
        sa.Column("resolved_diagnostic_tag", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("answers", "resolved_diagnostic_tag")
    op.drop_column("answers", "selected_option_id")
    op.execute("UPDATE answers SET value = '' WHERE value IS NULL")
    op.alter_column("answers", "value", existing_type=sa.Text(), nullable=False)

    op.execute("UPDATE questions SET answer_key = '' WHERE answer_key IS NULL")
    op.alter_column("questions", "answer_key", existing_type=sa.Text(), nullable=False)
    op.drop_column("questions", "text_distractors")
    op.drop_column("questions", "options")
    op.drop_column("questions", "correct_option_id")
    op.drop_column("questions", "question_type")
