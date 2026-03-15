from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.value_objects.questions import (
    DiagnosticTag,
    QuestionType,
    TextMatchMode,
)
from src.domain.value_objects.statuses import CriticalityLevel, MicroSkillStatus


class QuestionOptionCreateRequest(BaseModel):
    option_id: str
    text: str
    position: int = Field(ge=1)
    diagnostic_tag: DiagnosticTag | None = None


class TextDistractorCreateRequest(BaseModel):
    pattern: str
    match_mode: TextMatchMode = TextMatchMode.EXACT
    diagnostic_tag: DiagnosticTag = DiagnosticTag.OTHER


class QuestionCreateRequest(BaseModel):
    node_id: str
    text: str
    question_type: QuestionType = QuestionType.TEXT
    answer_key: str | None = None
    correct_option_id: str | None = None
    options: list[QuestionOptionCreateRequest] = Field(default_factory=list)
    text_distractors: list[TextDistractorCreateRequest] = Field(default_factory=list)
    max_score: int = 1


class CreateTestRequest(BaseModel):
    subject_code: str
    grade: int = Field(ge=1, le=4)
    questions: list[QuestionCreateRequest]


class QuestionResponse(BaseModel):
    question_id: UUID
    node_id: str
    text: str
    question_type: QuestionType
    max_score: int
    options: list[QuestionOptionResponse] = Field(default_factory=list)


class QuestionOptionResponse(BaseModel):
    option_id: str
    text: str
    position: int


class TestResponse(BaseModel):
    test_id: UUID
    subject_code: str
    grade: int
    version: int
    questions: list[QuestionResponse]


class AssignTestRequest(BaseModel):
    test_id: UUID
    child_id: UUID
    retake: bool = False


class AssignmentResponse(BaseModel):
    assignment_id: UUID
    test_id: UUID
    child_id: UUID
    status: str
    attempt_no: int


class AssignmentListItemResponse(BaseModel):
    assignment_id: UUID
    test_id: UUID
    test_title: str | None = None
    status: str
    attempt_no: int
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
    value: str | None = None
    selected_option_id: str | None = None
    time_spent_ms: int | None = Field(default=None, ge=0)


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
    value: str | None
    selected_option_id: str | None
    resolved_diagnostic_tag: DiagnosticTag | None
    time_spent_ms: int | None = None
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


class ContentImportDetails(BaseModel):
    subjects_created: int = 0
    subjects_updated: int = 0
    topics_created: int = 0
    topics_updated: int = 0
    micro_skills_created: int = 0
    micro_skills_updated: int = 0
    tests_created: int = 0
    tests_updated: int = 0
    tests_failed: int = 0
    questions_failed: int = 0


class ContentImportResponse(BaseModel):
    import_id: str
    source_id: str
    imported: int
    status: str
    errors: list[ContentImportIssue] = Field(default_factory=list)
    warnings: list[ContentImportIssue] = Field(default_factory=list)
    details: ContentImportDetails | None = None


class FixtureCleanupRequest(BaseModel):
    dry_run: bool = True
    subject_code_patterns: list[str] = Field(
        default_factory=lambda: [r"^math_v\d{2}.*$"]
    )
    topic_code_patterns: list[str] = Field(default_factory=lambda: [r"^MV\d{2}.*$"])
    node_id_patterns: list[str] = Field(default_factory=lambda: [r"^MV\d{2}.*$"])


class FixtureCleanupFiltersResponse(BaseModel):
    subject_code_patterns: list[str]
    topic_code_patterns: list[str]
    node_id_patterns: list[str]


class FixtureCleanupCountsResponse(BaseModel):
    subjects: int
    topics: int
    micro_skills: int
    tests: int
    questions: int
    assignments: int
    attempts: int
    answers: int


class FixtureCleanupResponse(BaseModel):
    status: Literal["planned", "completed"]
    dry_run: bool
    filters: FixtureCleanupFiltersResponse
    matched: FixtureCleanupCountsResponse
    deleted: FixtureCleanupCountsResponse


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
    topic_code: str
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
    question_type: QuestionType = QuestionType.TEXT
    answer_key: str | None = None
    correct_option_id: str | None = None
    options: list[QuestionOptionCreateRequest] = Field(default_factory=list)
    text_distractors: list[TextDistractorCreateRequest] = Field(default_factory=list)
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


class ChildResultsDiagnosticTagCountResponse(BaseModel):
    tag: DiagnosticTag
    count: int


class ChildResultsAttemptResponse(BaseModel):
    attempt_id: str
    assignment_id: str
    status: str
    score: int
    started_at: datetime
    submitted_at: datetime | None
    duration_seconds: int | None
    answers_total: int
    expected_answers_total: int
    unanswered_answers_total: int
    correct_answers: int
    accuracy_percent: float
    time_spent_ms_total: int
    avg_time_per_answer_ms: int | None
    has_resolved_diagnostics: bool
    resolved_diagnostic_tags: list[ChildResultsDiagnosticTagCountResponse] = Field(
        default_factory=list
    )


class ChildResultsSummaryResponse(BaseModel):
    attempts_total: int
    submitted_attempts_total: int
    started_attempts_total: int
    attempts_with_diagnostics_total: int
    answers_total: int
    expected_answers_total: int
    correct_answers_total: int
    accuracy_percent: float
    time_spent_ms_total: int
    avg_time_per_answer_ms: int | None
    resolved_diagnostic_tags: list[ChildResultsDiagnosticTagCountResponse] = Field(
        default_factory=list
    )


class ChildResultsResponse(BaseModel):
    child_id: UUID
    summary: ChildResultsSummaryResponse
    attempts: list[ChildResultsAttemptResponse] = Field(default_factory=list)


class ChildSkillResultResponse(BaseModel):
    node_id: str
    topic_code: str | None
    skill_name: str
    attempted_questions: int
    correct_answers: int
    accuracy_percent: float
    avg_time_per_answer_ms: int | None
    wilson_low: float
    wilson_high: float
    gap_level: Literal["insufficient_data", "high", "medium", "low"]
    resolved_diagnostic_tags: list[ChildResultsDiagnosticTagCountResponse] = Field(
        default_factory=list
    )
    recommendation: str


class ChildSkillResultsSummaryResponse(BaseModel):
    total_skills: int
    high_gap_total: int
    medium_gap_total: int
    low_gap_total: int
    insufficient_data_total: int


class ChildSkillResultsResponse(BaseModel):
    child_id: UUID
    summary: ChildSkillResultsSummaryResponse
    skills: list[ChildSkillResultResponse] = Field(default_factory=list)


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
    topic_code: str
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
    topic_code: str | None
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
