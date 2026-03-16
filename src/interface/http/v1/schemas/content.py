from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.application.contracts.questions import (
    DiagnosticTag,
    QuestionType,
    TextMatchMode,
)
from src.application.contracts.statuses import CriticalityLevel, MicroSkillStatus


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


class QuestionOptionResponse(BaseModel):
    option_id: str
    text: str
    position: int


class QuestionResponse(BaseModel):
    question_id: UUID
    node_id: str
    text: str
    question_type: QuestionType
    max_score: int
    options: list[QuestionOptionResponse] = Field(default_factory=list)


class TestResponse(BaseModel):
    test_id: UUID
    subject_code: str
    grade: int
    version: int
    questions: list[QuestionResponse]


class PublishTestResponse(BaseModel):
    test_id: UUID
    status: str


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


class MicroSkillUpdateRequest(BaseModel):
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
