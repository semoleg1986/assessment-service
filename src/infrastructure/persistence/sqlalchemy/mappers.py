from __future__ import annotations

from src.domain.content.micro_skill.entity import MicroSkillNode
from src.domain.content.subject.entity import Subject
from src.domain.content.test.entity import AssessmentTest
from src.domain.content.test.question import Question
from src.domain.content.test.question_option import QuestionOption
from src.domain.content.test.text_distractor import TextDistractor
from src.domain.content.topic.entity import Topic
from src.domain.delivery.assignment.entity import AssignmentAggregate
from src.domain.delivery.attempt.answer import Answer
from src.domain.delivery.attempt.entity import AttemptAggregate
from src.domain.shared.questions import DiagnosticTag, QuestionType, TextMatchMode
from src.domain.shared.statuses import (
    AssignmentStatus,
    AttemptStatus,
    CriticalityLevel,
    MicroSkillStatus,
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


def _to_int(value: object, *, default: int = 0) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


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
        topic_code=model.topic_code,
        section_code=model.section_code,
        section_name=model.section_name,
        micro_skill_name=model.micro_skill_name,
        predecessor_ids=list(model.predecessor_ids or []),
        criticality=CriticalityLevel(model.criticality),
        source_ref=model.source_ref,
        description=model.description,
        status=MicroSkillStatus(model.status),
        external_ref=model.external_ref,
        version=model.version,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def question_from_model(model: QuestionModel) -> Question:
    options = [
        QuestionOption(
            option_id=str(item.get("option_id", "")),
            text=str(item.get("text", "")),
            position=_to_int(item.get("position", 0), default=0),
            diagnostic_tag=(
                DiagnosticTag(str(item.get("diagnostic_tag")))
                if item.get("diagnostic_tag")
                else None
            ),
        )
        for item in (model.options or [])
    ]
    text_distractors = [
        TextDistractor(
            pattern=str(item.get("pattern", "")),
            match_mode=TextMatchMode(str(item.get("match_mode", "exact"))),
            diagnostic_tag=DiagnosticTag(str(item.get("diagnostic_tag", "other"))),
        )
        for item in (model.text_distractors or [])
    ]
    return Question(
        question_id=model.question_id,
        node_id=model.node_id,
        text=model.text,
        question_type=QuestionType(model.question_type),
        answer_key=model.answer_key,
        correct_option_id=model.correct_option_id,
        options=options,
        text_distractors=text_distractors,
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
        attempt_no=model.attempt_no,
    )


def answers_from_attempt_model(model: AttemptModel) -> list[Answer]:
    return [
        Answer(
            question_id=a.question_id,
            value=a.value,
            selected_option_id=a.selected_option_id,
            resolved_diagnostic_tag=(
                DiagnosticTag(a.resolved_diagnostic_tag)
                if a.resolved_diagnostic_tag is not None
                else None
            ),
            time_spent_ms=a.time_spent_ms,
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
