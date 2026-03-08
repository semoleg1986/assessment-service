from __future__ import annotations

from src.domain.aggregates.assignment import AssignmentAggregate
from src.domain.aggregates.attempt import AttemptAggregate
from src.domain.aggregates.test_aggregate import AssessmentTest
from src.domain.entities.answer import Answer
from src.domain.entities.micro_skill_node import MicroSkillNode
from src.domain.entities.question import Question
from src.domain.entities.subject import Subject
from src.domain.entities.topic import Topic
from src.domain.value_objects.statuses import (
    AssignmentStatus,
    AttemptStatus,
    CriticalityLevel,
)
from src.infrastructure.persistence.sqlalchemy.models import (
    AssignmentModel,
    AttemptModel,
    MicroSkillNodeModel,
    QuestionModel,
    SubjectModel,
    TestModel,
    TopicModel,
)


def subject_from_model(model: SubjectModel) -> Subject:
    return Subject(code=model.code, name=model.name)


def topic_from_model(model: TopicModel) -> Topic:
    return Topic(
        code=model.code,
        subject_code=model.subject_code,
        grade=model.grade,
        name=model.name,
    )


def micro_skill_from_model(model: MicroSkillNodeModel) -> MicroSkillNode:
    return MicroSkillNode(
        node_id=model.node_id,
        subject_code=model.subject_code,
        grade=model.grade,
        section_code=model.section_code,
        section_name=model.section_name,
        micro_skill_name=model.micro_skill_name,
        predecessor_ids=list(model.predecessor_ids or []),
        criticality=CriticalityLevel(model.criticality),
        source_ref=model.source_ref,
    )


def question_from_model(model: QuestionModel) -> Question:
    return Question(
        question_id=model.question_id,
        node_id=model.node_id,
        text=model.text,
        answer_key=model.answer_key,
        max_score=model.max_score,
    )


def assessment_test_from_model(model: TestModel) -> AssessmentTest:
    questions = [
        question_from_model(q)
        for q in sorted(model.questions, key=lambda x: str(x.question_id))
    ]
    return AssessmentTest(
        test_id=model.test_id,
        subject_code=model.subject_code,
        grade=model.grade,
        questions=questions,
        created_at=model.created_at,
        version=model.version,
    )


def assignment_from_model(model: AssignmentModel) -> AssignmentAggregate:
    return AssignmentAggregate(
        assignment_id=model.assignment_id,
        test_id=model.test_id,
        child_id=model.child_id,
        status=AssignmentStatus(model.status),
        assigned_at=model.assigned_at,
        version=model.version,
    )


def answers_from_attempt_model(model: AttemptModel) -> list[Answer]:
    return [
        Answer(
            question_id=a.question_id,
            value=a.value,
            is_correct=a.is_correct,
            awarded_score=a.awarded_score,
        )
        for a in sorted(model.answers, key=lambda x: x.answer_id)
    ]


def attempt_from_model(model: AttemptModel) -> AttemptAggregate:
    return AttemptAggregate(
        attempt_id=model.attempt_id,
        assignment_id=model.assignment_id,
        child_id=model.child_id,
        status=AttemptStatus(model.status),
        started_at=model.started_at,
        submitted_at=model.submitted_at,
        score=model.score,
        answers=answers_from_attempt_model(model),
        version=model.version,
    )
