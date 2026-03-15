from __future__ import annotations

from src.domain.content.micro_skill.entity import MicroSkillNode
from src.domain.content.test.entity import AssessmentTest
from src.domain.content.test.question import Question
from src.domain.shared.questions import DiagnosticTag
from src.interface.http.v1.schemas import (
    ChildResultsDiagnosticTagCountResponse,
    FixtureCleanupCountsResponse,
    MicroSkillResponse,
    QuestionOptionResponse,
    QuestionResponse,
    TestResponse,
)


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


def question_response(question: Question) -> QuestionResponse:
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


def test_response(test: AssessmentTest) -> TestResponse:
    return TestResponse(
        test_id=test.test_id,
        subject_code=test.subject_code,
        grade=test.grade,
        version=test.version,
        questions=[question_response(question) for question in test.questions],
    )


def micro_skill_response(
    node: MicroSkillNode, *, blocks_count: int
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
