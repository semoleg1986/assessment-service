from __future__ import annotations

from typing import cast
from uuid import UUID

from src.application.facade import (
    AssignTestInput,
    ChildScopedInput,
    CleanupFixturesInput,
    CreateSubjectInput,
    CreateTestInput,
    CreateTopicInput,
    LinkMicroSkillPredecessorsInput,
    TestQuestionData,
    TestQuestionOptionData,
    TestTextDistractorData,
    UpsertMicroSkillInput,
)
from src.interface.http.v1.schemas import (
    AssignTestRequest,
    CreateTestRequest,
    FixtureCleanupRequest,
    MicroSkillCreateRequest,
    MicroSkillLinkRequest,
    MicroSkillUpdateRequest,
    SubjectCreateRequest,
    TopicCreateRequest,
)


def to_create_subject_input(body: SubjectCreateRequest) -> CreateSubjectInput:
    return CreateSubjectInput(code=body.code, name=body.name)


def to_create_topic_input(body: TopicCreateRequest) -> CreateTopicInput:
    return CreateTopicInput(
        code=body.code,
        subject_code=body.subject_code,
        grade=body.grade,
        name=body.name,
    )


def to_create_micro_skill_input(body: MicroSkillCreateRequest) -> UpsertMicroSkillInput:
    return UpsertMicroSkillInput(
        node_id=body.node_id,
        subject_code=body.subject_code,
        topic_code=body.topic_code,
        grade=body.grade,
        section_code=body.section_code,
        section_name=body.section_name,
        micro_skill_name=body.micro_skill_name,
        predecessor_ids=body.predecessor_ids,
        criticality=body.criticality,
        source_ref=body.source_ref,
        description=body.description,
        status=body.status,
        external_ref=body.external_ref,
    )


def to_update_micro_skill_input(
    *, node_id: str, body: MicroSkillUpdateRequest
) -> UpsertMicroSkillInput:
    return UpsertMicroSkillInput(
        node_id=node_id,
        subject_code=body.subject_code,
        topic_code=body.topic_code,
        grade=body.grade,
        section_code=body.section_code,
        section_name=body.section_name,
        micro_skill_name=body.micro_skill_name,
        predecessor_ids=body.predecessor_ids,
        criticality=body.criticality,
        source_ref=body.source_ref,
        description=body.description,
        status=body.status,
        external_ref=body.external_ref,
    )


def to_upsert_micro_skill_input(
    *,
    node_id: str | None = None,
    body: MicroSkillCreateRequest | MicroSkillUpdateRequest,
) -> UpsertMicroSkillInput:
    if node_id is None:
        create_body = cast(MicroSkillCreateRequest, body)
        return to_create_micro_skill_input(create_body)
    update_body = cast(MicroSkillUpdateRequest, body)
    return to_update_micro_skill_input(node_id=node_id, body=update_body)


def to_link_micro_skill_predecessors_input(
    *, node_id: str, body: MicroSkillLinkRequest
) -> LinkMicroSkillPredecessorsInput:
    return LinkMicroSkillPredecessorsInput(
        node_id=node_id,
        predecessor_ids=body.predecessor_ids,
    )


def to_create_test_input(body: CreateTestRequest) -> CreateTestInput:
    return CreateTestInput(
        subject_code=body.subject_code,
        grade=body.grade,
        questions=[
            TestQuestionData(
                node_id=question.node_id,
                text=question.text,
                question_type=question.question_type,
                answer_key=question.answer_key,
                correct_option_id=question.correct_option_id,
                options=[
                    TestQuestionOptionData(
                        option_id=option.option_id,
                        text=option.text,
                        position=option.position,
                        diagnostic_tag=option.diagnostic_tag,
                    )
                    for option in question.options
                ],
                text_distractors=[
                    TestTextDistractorData(
                        pattern=distractor.pattern,
                        match_mode=distractor.match_mode,
                        diagnostic_tag=distractor.diagnostic_tag,
                    )
                    for distractor in question.text_distractors
                ],
                max_score=question.max_score,
            )
            for question in body.questions
        ],
    )


def to_assign_test_input(body: AssignTestRequest) -> AssignTestInput:
    return AssignTestInput(
        test_id=body.test_id,
        child_id=body.child_id,
        retake=body.retake,
    )


def to_cleanup_fixtures_input(body: FixtureCleanupRequest) -> CleanupFixturesInput:
    return CleanupFixturesInput(
        dry_run=body.dry_run,
        subject_code_patterns=tuple(body.subject_code_patterns),
        topic_code_patterns=tuple(body.topic_code_patterns),
        node_id_patterns=tuple(body.node_id_patterns),
    )


def to_child_scoped_input(*, child_id: UUID) -> ChildScopedInput:
    return ChildScopedInput(child_id=child_id)
