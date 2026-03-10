from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from src.application.ports.unit_of_work import UnitOfWork
from src.infrastructure.persistence.sqlalchemy.models import (
    AnswerModel,
    AssignmentModel,
    AttemptModel,
    MicroSkillNodeModel,
    QuestionModel,
    SubjectModel,
    TestModel,
    TopicModel,
)
from src.infrastructure.persistence.sqlalchemy.uow import SqlAlchemyUnitOfWork

DEFAULT_SUBJECT_CODE_PATTERNS: tuple[str, ...] = (r"^math_v\d{2}.*$",)
DEFAULT_TOPIC_CODE_PATTERNS: tuple[str, ...] = (r"^MV\d{2}.*$",)
DEFAULT_NODE_ID_PATTERNS: tuple[str, ...] = (r"^MV\d{2}.*$",)


@dataclass(frozen=True)
class FixtureCleanupFilters:
    subject_code_patterns: tuple[str, ...] = DEFAULT_SUBJECT_CODE_PATTERNS
    topic_code_patterns: tuple[str, ...] = DEFAULT_TOPIC_CODE_PATTERNS
    node_id_patterns: tuple[str, ...] = DEFAULT_NODE_ID_PATTERNS


@dataclass(frozen=True)
class FixtureCleanupCounts:
    subjects: int = 0
    topics: int = 0
    micro_skills: int = 0
    tests: int = 0
    questions: int = 0
    assignments: int = 0
    attempts: int = 0
    answers: int = 0


@dataclass(frozen=True)
class FixtureCleanupExecution:
    dry_run: bool
    filters: FixtureCleanupFilters
    matched: FixtureCleanupCounts
    deleted: FixtureCleanupCounts


@dataclass(frozen=True)
class _FixtureCleanupPlan:
    subjects: tuple[str, ...]
    topics: tuple[str, ...]
    micro_skills: tuple[str, ...]
    tests: tuple[UUID, ...]
    questions: tuple[UUID, ...]
    assignments: tuple[UUID, ...]
    attempts: tuple[UUID, ...]
    answers: int

    def to_counts(self) -> FixtureCleanupCounts:
        return FixtureCleanupCounts(
            subjects=len(self.subjects),
            topics=len(self.topics),
            micro_skills=len(self.micro_skills),
            tests=len(self.tests),
            questions=len(self.questions),
            assignments=len(self.assignments),
            attempts=len(self.attempts),
            answers=self.answers,
        )


class FixtureCleanupUnsupportedError(RuntimeError):
    pass


def _compile_patterns(
    patterns: tuple[str, ...], *, label: str
) -> list[re.Pattern[str]]:
    compiled: list[re.Pattern[str]] = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern))
        except re.error as exc:
            raise ValueError(f"Invalid regex in {label}: {pattern}") from exc
    return compiled


def _matches_any(value: str, patterns: list[re.Pattern[str]]) -> bool:
    return any(pattern.search(value) for pattern in patterns)


def _build_cleanup_plan(
    *, session: Session, filters: FixtureCleanupFilters
) -> _FixtureCleanupPlan:
    subject_patterns = _compile_patterns(
        filters.subject_code_patterns, label="subject_code_patterns"
    )
    topic_patterns = _compile_patterns(
        filters.topic_code_patterns, label="topic_code_patterns"
    )
    node_patterns = _compile_patterns(
        filters.node_id_patterns, label="node_id_patterns"
    )

    subject_codes = tuple(
        code
        for code in session.scalars(select(SubjectModel.code)).all()
        if _matches_any(code, subject_patterns)
    )
    subject_code_set = set(subject_codes)

    topic_rows = session.execute(select(TopicModel.code, TopicModel.subject_code)).all()
    topic_codes = tuple(
        code
        for code, subject_code in topic_rows
        if subject_code in subject_code_set or _matches_any(code, topic_patterns)
    )
    topic_code_set = set(topic_codes)

    micro_skill_rows = session.execute(
        select(
            MicroSkillNodeModel.node_id,
            MicroSkillNodeModel.subject_code,
            MicroSkillNodeModel.topic_code,
        )
    ).all()
    micro_skill_ids = tuple(
        node_id
        for node_id, subject_code, topic_code in micro_skill_rows
        if (
            subject_code in subject_code_set
            or _matches_any(node_id, node_patterns)
            or (topic_code is not None and topic_code in topic_code_set)
        )
    )
    micro_skill_id_set = set(micro_skill_ids)

    test_rows = session.execute(select(TestModel.test_id, TestModel.subject_code)).all()
    test_ids = tuple(
        test_id
        for test_id, subject_code in test_rows
        if subject_code in subject_code_set
    )
    test_id_set = set(test_ids)

    question_rows = session.execute(
        select(QuestionModel.question_id, QuestionModel.test_id, QuestionModel.node_id)
    ).all()
    question_ids = tuple(
        question_id
        for question_id, test_id, node_id in question_rows
        if test_id in test_id_set or node_id in micro_skill_id_set
    )
    question_test_ids = {
        test_id
        for _, test_id, node_id in question_rows
        if node_id in micro_skill_id_set
    }
    if question_test_ids:
        test_id_set.update(question_test_ids)
        test_ids = tuple(sorted(test_id_set, key=str))

    assignment_rows = session.execute(
        select(AssignmentModel.assignment_id, AssignmentModel.test_id)
    ).all()
    assignment_ids = tuple(
        assignment_id
        for assignment_id, test_id in assignment_rows
        if test_id in test_id_set
    )
    assignment_id_set = set(assignment_ids)

    attempt_rows = session.execute(
        select(AttemptModel.attempt_id, AttemptModel.assignment_id)
    ).all()
    attempt_ids = tuple(
        attempt_id
        for attempt_id, assignment_id in attempt_rows
        if assignment_id in assignment_id_set
    )
    answer_count = 0
    if attempt_ids:
        answer_count = len(
            session.scalars(
                select(AnswerModel.answer_id).where(
                    AnswerModel.attempt_id.in_(attempt_ids)
                )
            ).all()
        )

    return _FixtureCleanupPlan(
        subjects=tuple(sorted(subject_code_set)),
        topics=tuple(sorted(topic_code_set)),
        micro_skills=tuple(sorted(micro_skill_id_set)),
        tests=tuple(sorted(test_id_set, key=str)),
        questions=tuple(sorted(question_ids, key=str)),
        assignments=tuple(sorted(assignment_id_set, key=str)),
        attempts=tuple(sorted(attempt_ids, key=str)),
        answers=answer_count,
    )


def _rowcount(value: int | None) -> int:
    if value is None:
        return 0
    return value


def _delete_uuid_set(
    *,
    session: Session,
    model: type[Any],
    column: Any,
    values: tuple[UUID, ...],
) -> int:
    if not values:
        return 0
    result = session.execute(delete(model).where(column.in_(values)))
    return _rowcount(cast(CursorResult[Any], result).rowcount)


def _delete_str_set(
    *,
    session: Session,
    model: type[Any],
    column: Any,
    values: tuple[str, ...],
) -> int:
    if not values:
        return 0
    result = session.execute(delete(model).where(column.in_(values)))
    return _rowcount(cast(CursorResult[Any], result).rowcount)


def run_fixture_cleanup(
    *,
    uow: UnitOfWork,
    dry_run: bool,
    filters: FixtureCleanupFilters,
) -> FixtureCleanupExecution:
    if not isinstance(uow, SqlAlchemyUnitOfWork):
        raise FixtureCleanupUnsupportedError(
            "Fixture cleanup requires SQLAlchemy UnitOfWork (DATABASE_URL must be set)"
        )

    session = uow.session()
    plan = _build_cleanup_plan(session=session, filters=filters)
    matched = plan.to_counts()
    deleted = FixtureCleanupCounts()

    if not dry_run:
        deleted = FixtureCleanupCounts(
            answers=_delete_uuid_set(
                session=session,
                model=AnswerModel,
                column=AnswerModel.attempt_id,
                values=plan.attempts,
            ),
            attempts=_delete_uuid_set(
                session=session,
                model=AttemptModel,
                column=AttemptModel.attempt_id,
                values=plan.attempts,
            ),
            assignments=_delete_uuid_set(
                session=session,
                model=AssignmentModel,
                column=AssignmentModel.assignment_id,
                values=plan.assignments,
            ),
            questions=_delete_uuid_set(
                session=session,
                model=QuestionModel,
                column=QuestionModel.question_id,
                values=plan.questions,
            ),
            tests=_delete_uuid_set(
                session=session,
                model=TestModel,
                column=TestModel.test_id,
                values=plan.tests,
            ),
            micro_skills=_delete_str_set(
                session=session,
                model=MicroSkillNodeModel,
                column=MicroSkillNodeModel.node_id,
                values=plan.micro_skills,
            ),
            topics=_delete_str_set(
                session=session,
                model=TopicModel,
                column=TopicModel.code,
                values=plan.topics,
            ),
            subjects=_delete_str_set(
                session=session,
                model=SubjectModel,
                column=SubjectModel.code,
                values=plan.subjects,
            ),
        )
        uow.commit()

    return FixtureCleanupExecution(
        dry_run=dry_run,
        filters=filters,
        matched=matched,
        deleted=deleted,
    )
