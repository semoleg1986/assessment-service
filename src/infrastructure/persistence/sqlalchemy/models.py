from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# mypy: disable-error-code=misc


class Base(DeclarativeBase):
    pass


class SubjectModel(Base):
    __tablename__ = "subjects"

    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class TopicModel(Base):
    __tablename__ = "topics"

    code: Mapped[str] = mapped_column(String(128), primary_key=True)
    subject_code: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("subjects.code", ondelete="CASCADE"),
        nullable=False,
    )
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class MicroSkillNodeModel(Base):
    __tablename__ = "micro_skill_nodes"

    node_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    subject_code: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("subjects.code", ondelete="CASCADE"),
        nullable=False,
    )
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    section_code: Mapped[str] = mapped_column(String(64), nullable=False)
    section_name: Mapped[str] = mapped_column(String(255), nullable=False)
    micro_skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    predecessor_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    criticality: Mapped[str] = mapped_column(String(32), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)


class TestModel(Base):
    __tablename__ = "tests"

    test_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    subject_code: Mapped[str] = mapped_column(String(64), nullable=False)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    questions: Mapped[list[QuestionModel]] = relationship(
        back_populates="test",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class QuestionModel(Base):
    __tablename__ = "questions"

    question_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    test_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("tests.test_id", ondelete="CASCADE"),
        nullable=False,
    )
    node_id: Mapped[str] = mapped_column(String(128), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_key: Mapped[str] = mapped_column(Text, nullable=False)
    max_score: Mapped[int] = mapped_column(Integer, nullable=False)

    test: Mapped[TestModel] = relationship(back_populates="questions")


class AssignmentModel(Base):
    __tablename__ = "assignments"

    assignment_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    test_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("tests.test_id", ondelete="RESTRICT"),
        nullable=False,
    )
    child_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)


class AttemptModel(Base):
    __tablename__ = "attempts"

    attempt_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    assignment_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("assignments.assignment_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    child_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    answers: Mapped[list[AnswerModel]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class AnswerModel(Base):
    __tablename__ = "answers"

    answer_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    attempt_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("attempts.attempt_id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(nullable=False)
    awarded_score: Mapped[int] = mapped_column(Integer, nullable=False)

    attempt: Mapped[AttemptModel] = relationship(back_populates="answers")
