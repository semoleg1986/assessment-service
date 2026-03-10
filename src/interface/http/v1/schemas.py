from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.value_objects.statuses import CriticalityLevel, MicroSkillStatus


class QuestionCreateRequest(BaseModel):
    node_id: str
    text: str
    answer_key: str
    max_score: int = 1


class CreateTestRequest(BaseModel):
    subject_code: str
    grade: int = Field(ge=1, le=4)
    questions: list[QuestionCreateRequest]


class QuestionResponse(BaseModel):
    question_id: UUID
    node_id: str
    text: str
    max_score: int


class TestResponse(BaseModel):
    test_id: UUID
    subject_code: str
    grade: int
    version: int
    questions: list[QuestionResponse]


class AssignTestRequest(BaseModel):
    test_id: UUID
    child_id: UUID


class AssignmentResponse(BaseModel):
    assignment_id: UUID
    test_id: UUID
    child_id: UUID
    status: str


class AssignmentListItemResponse(BaseModel):
    assignment_id: UUID
    test_id: UUID
    test_title: str | None = None
    status: str
    due_at: str | None = None


class StartAttemptRequest(BaseModel):
    assignment_id: UUID
    child_id: UUID


class StartAttemptResponse(BaseModel):
    attempt_id: UUID
    assignment_id: UUID
    child_id: UUID
    status: str


class SubmittedAnswerRequest(BaseModel):
    question_id: UUID
    value: str


class SubmitAttemptRequest(BaseModel):
    answers: list[SubmittedAnswerRequest]


class SubmitAttemptResponse(BaseModel):
    attempt_id: str
    status: str
    score: int
    max_score: int
    signal: str


class SaveAttemptAnswersRequest(BaseModel):
    answers: list[SubmittedAnswerRequest]


class SaveAttemptAnswersResponse(BaseModel):
    attempt_id: str
    saved_answers: int


class AttemptAnswerResponse(BaseModel):
    question_id: str
    value: str
    is_correct: bool
    awarded_score: int


class AttemptResultResponse(BaseModel):
    attempt_id: str
    status: str
    score: int
    answers: list[AttemptAnswerResponse]


class StartAttemptByAssignmentRequest(BaseModel):
    child_id: UUID


class ContentImportRequest(BaseModel):
    source_id: str
    contract_version: str
    validate_only: bool = False
    error_mode: Literal["collect", "fail_fast"] = "collect"
    payload: ContentImportPayload


class ContentImportIssue(BaseModel):
    code: str
    message: str
    path: str


class ContentImportResponse(BaseModel):
    import_id: str
    source_id: str
    imported: int
    status: str
    errors: list[ContentImportIssue] = Field(default_factory=list)
    warnings: list[ContentImportIssue] = Field(default_factory=list)
    details: dict[str, int] | None = None


class ContentImportSubjectItem(BaseModel):
    code: str
    name: str


class ContentImportTopicItem(BaseModel):
    code: str
    subject_code: str
    grade: int = Field(ge=1, le=11)
    name: str


class ContentImportMicroSkillItem(BaseModel):
    node_id: str
    subject_code: str
    grade: int = Field(ge=1, le=11)
    section_code: str
    section_name: str
    micro_skill_name: str
    predecessor_ids: list[str] = Field(default_factory=list)
    criticality: CriticalityLevel = CriticalityLevel.MEDIUM
    source_ref: str | None = None
    description: str | None = None
    status: MicroSkillStatus = MicroSkillStatus.ACTIVE
    external_ref: str | None = None


class ContentImportQuestionItem(BaseModel):
    external_id: str
    node_id: str
    text: str
    answer_key: str
    max_score: int = Field(default=1, ge=1)


class ContentImportTestItem(BaseModel):
    external_id: str
    subject_code: str
    grade: int = Field(ge=1, le=4)
    questions: list[ContentImportQuestionItem] = Field(min_length=1)


class ContentImportPayload(BaseModel):
    subjects: list[ContentImportSubjectItem] = Field(default_factory=list)
    topics: list[ContentImportTopicItem] = Field(default_factory=list)
    micro_skills: list[ContentImportMicroSkillItem] = Field(default_factory=list)
    tests: list[ContentImportTestItem] = Field(default_factory=list)


class PublishTestResponse(BaseModel):
    test_id: UUID
    status: str


class ChildDiagnosticsResponse(BaseModel):
    child_id: UUID
    assignments_total: int
    attempts_total: int


class SubjectCreateRequest(BaseModel):
    code: str
    name: str


class SubjectResponse(BaseModel):
    code: str
    name: str


class TopicCreateRequest(BaseModel):
    code: str
    subject_code: str
    grade: int = Field(ge=1, le=11)
    name: str


class TopicResponse(BaseModel):
    code: str
    subject_code: str
    grade: int
    name: str


class MicroSkillCreateRequest(BaseModel):
    node_id: str
    subject_code: str
    grade: int = Field(ge=1, le=11)
    section_code: str
    section_name: str
    micro_skill_name: str
    predecessor_ids: list[str] = Field(default_factory=list)
    criticality: CriticalityLevel = CriticalityLevel.MEDIUM
    source_ref: str | None = None
    description: str | None = None
    status: MicroSkillStatus = MicroSkillStatus.ACTIVE
    external_ref: str | None = None


class MicroSkillLinkRequest(BaseModel):
    predecessor_ids: list[str]


class MicroSkillResponse(BaseModel):
    node_id: str
    subject_code: str
    grade: int
    section_code: str
    section_name: str
    micro_skill_name: str
    predecessor_ids: list[str]
    criticality: CriticalityLevel
    source_ref: str | None
    description: str | None
    status: MicroSkillStatus
    external_ref: str | None
    version: int
    created_at: datetime
    updated_at: datetime
    blocks_count: int
