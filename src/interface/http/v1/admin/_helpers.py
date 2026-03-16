from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence
from uuid import UUID

from src.application.contracts.questions import DiagnosticTag, QuestionType
from src.application.contracts.statuses import CriticalityLevel, MicroSkillStatus
from src.interface.http.v1.schemas import (
    ChildResultsDiagnosticTagCountResponse,
    FixtureCleanupCountsResponse,
    MicroSkillResponse,
    QuestionOptionResponse,
    QuestionResponse,
    TestResponse,
)


class _QuestionOptionView(Protocol):
    @property
    def option_id(self) -> str: ...

    @property
    def text(self) -> str: ...

    @property
    def position(self) -> int: ...


class _QuestionView(Protocol):
    @property
    def question_id(self) -> UUID: ...

    @property
    def node_id(self) -> str: ...

    @property
    def text(self) -> str: ...

    @property
    def question_type(self) -> QuestionType: ...

    @property
    def max_score(self) -> int: ...

    @property
    def options(self) -> Sequence[_QuestionOptionView]: ...


class _TestView(Protocol):
    @property
    def test_id(self) -> UUID: ...

    @property
    def subject_code(self) -> str: ...

    @property
    def grade(self) -> int: ...

    @property
    def version(self) -> int: ...

    @property
    def questions(self) -> Sequence[_QuestionView]: ...


class _MicroSkillView(Protocol):
    @property
    def node_id(self) -> str: ...

    @property
    def subject_code(self) -> str: ...

    @property
    def topic_code(self) -> str | None: ...

    @property
    def grade(self) -> int: ...

    @property
    def section_code(self) -> str: ...

    @property
    def section_name(self) -> str: ...

    @property
    def micro_skill_name(self) -> str: ...

    @property
    def predecessor_ids(self) -> list[str]: ...

    @property
    def criticality(self) -> CriticalityLevel: ...

    @property
    def source_ref(self) -> str | None: ...

    @property
    def description(self) -> str | None: ...

    @property
    def status(self) -> MicroSkillStatus: ...

    @property
    def external_ref(self) -> str | None: ...

    @property
    def version(self) -> int: ...

    @property
    def created_at(self) -> datetime: ...

    @property
    def updated_at(self) -> datetime: ...


def sorted_diagnostic_tag_counts(
    counts: dict[str, int],
) -> list[ChildResultsDiagnosticTagCountResponse]:
    return [
        ChildResultsDiagnosticTagCountResponse(tag=DiagnosticTag(tag), count=count)
        for tag, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]


def cleanup_counts_response(
    *,
    subjects: int,
    topics: int,
    micro_skills: int,
    tests: int,
    questions: int,
    assignments: int,
    attempts: int,
    answers: int,
) -> FixtureCleanupCountsResponse:
    return FixtureCleanupCountsResponse(
        subjects=subjects,
        topics=topics,
        micro_skills=micro_skills,
        tests=tests,
        questions=questions,
        assignments=assignments,
        attempts=attempts,
        answers=answers,
    )


def question_response(question: _QuestionView) -> QuestionResponse:
    return QuestionResponse(
        question_id=question.question_id,
        node_id=question.node_id,
        text=question.text,
        question_type=question.question_type,
        max_score=question.max_score,
        options=[
            QuestionOptionResponse(
                option_id=option.option_id,
                text=option.text,
                position=option.position,
            )
            for option in sorted(question.options, key=lambda item: item.position)
        ],
    )


def test_response(test: _TestView) -> TestResponse:
    return TestResponse(
        test_id=test.test_id,
        subject_code=test.subject_code,
        grade=test.grade,
        version=test.version,
        questions=[question_response(question) for question in test.questions],
    )


def micro_skill_response(
    node: _MicroSkillView, *, blocks_count: int
) -> MicroSkillResponse:
    return MicroSkillResponse(
        node_id=node.node_id,
        subject_code=node.subject_code,
        topic_code=node.topic_code,
        grade=node.grade,
        section_code=node.section_code,
        section_name=node.section_name,
        micro_skill_name=node.micro_skill_name,
        predecessor_ids=node.predecessor_ids,
        criticality=node.criticality,
        source_ref=node.source_ref,
        description=node.description,
        status=node.status,
        external_ref=node.external_ref,
        version=node.version,
        created_at=node.created_at,
        updated_at=node.updated_at,
        blocks_count=blocks_count,
    )
