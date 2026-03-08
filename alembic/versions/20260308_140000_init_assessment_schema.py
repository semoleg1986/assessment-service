"""init assessment schema

Revision ID: 20260308_140000
Revises:
Create Date: 2026-03-08 14:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision = "20260308_140000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subjects",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )

    op.create_table(
        "topics",
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("subject_code", sa.String(length=64), nullable=False),
        sa.Column("grade", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["subject_code"], ["subjects.code"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("code"),
    )

    op.create_table(
        "micro_skill_nodes",
        sa.Column("node_id", sa.String(length=128), nullable=False),
        sa.Column("subject_code", sa.String(length=64), nullable=False),
        sa.Column("grade", sa.Integer(), nullable=False),
        sa.Column("section_code", sa.String(length=64), nullable=False),
        sa.Column("section_name", sa.String(length=255), nullable=False),
        sa.Column("micro_skill_name", sa.String(length=255), nullable=False),
        sa.Column(
            "predecessor_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("criticality", sa.String(length=32), nullable=False),
        sa.Column("source_ref", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["subject_code"], ["subjects.code"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("node_id"),
    )

    op.create_table(
        "tests",
        sa.Column("test_id", sa.Uuid(), nullable=False),
        sa.Column("subject_code", sa.String(length=64), nullable=False),
        sa.Column("grade", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("test_id"),
    )

    op.create_table(
        "questions",
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("test_id", sa.Uuid(), nullable=False),
        sa.Column("node_id", sa.String(length=128), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("answer_key", sa.Text(), nullable=False),
        sa.Column("max_score", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["test_id"], ["tests.test_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("question_id"),
    )

    op.create_table(
        "assignments",
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("test_id", sa.Uuid(), nullable=False),
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["test_id"], ["tests.test_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("assignment_id"),
    )
    op.create_index(
        op.f("ix_assignments_child_id"), "assignments", ["child_id"], unique=False
    )

    op.create_table(
        "attempts",
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["assignments.assignment_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("attempt_id"),
    )
    op.create_index(
        op.f("ix_attempts_assignment_id"), "attempts", ["assignment_id"], unique=False
    )
    op.create_index(
        op.f("ix_attempts_child_id"), "attempts", ["child_id"], unique=False
    )

    op.create_table(
        "answers",
        sa.Column("answer_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("awarded_score", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["attempt_id"], ["attempts.attempt_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("answer_id"),
    )


def downgrade() -> None:
    op.drop_table("answers")
    op.drop_index(op.f("ix_attempts_child_id"), table_name="attempts")
    op.drop_index(op.f("ix_attempts_assignment_id"), table_name="attempts")
    op.drop_table("attempts")
    op.drop_index(op.f("ix_assignments_child_id"), table_name="assignments")
    op.drop_table("assignments")
    op.drop_table("questions")
    op.drop_table("tests")
    op.drop_table("micro_skill_nodes")
    op.drop_table("topics")
    op.drop_table("subjects")
