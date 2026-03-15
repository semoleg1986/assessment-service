from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.domain.shared.questions import QuestionType
from src.domain.shared.statuses import CriticalityLevel, MicroSkillStatus
from src.interface.http.v1.schemas.content import (
    QuestionOptionCreateRequest,
    TextDistractorCreateRequest,
)


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
