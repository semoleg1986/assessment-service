from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

from src.application.contracts.questions import (
    DiagnosticTag,
    QuestionType,
    TextMatchMode,
)
from src.domain.shared.statuses import CriticalityLevel, MicroSkillStatus


@dataclass(frozen=True, slots=True)
class TestQuestionOptionData:
    option_id: str
    text: str
    position: int
    diagnostic_tag: DiagnosticTag | None


@dataclass(frozen=True, slots=True)
class TestTextDistractorData:
    pattern: str
    match_mode: TextMatchMode
    diagnostic_tag: DiagnosticTag


@dataclass(frozen=True, slots=True)
class TestQuestionData:
    node_id: str
    text: str
    question_type: QuestionType
    answer_key: str | None
    correct_option_id: str | None
    options: list[TestQuestionOptionData]
    text_distractors: list[TestTextDistractorData]
    max_score: int


@dataclass(frozen=True, slots=True)
class SubmittedAnswerData:
    question_id: UUID
    value: str | None
    selected_option_id: str | None
    time_spent_ms: int | None


@dataclass(frozen=True, slots=True)
class CreateSubjectInput:
    code: str
    name: str


@dataclass(frozen=True, slots=True)
class CreateTopicInput:
    code: str
    subject_code: str
    grade: int
    name: str


@dataclass(frozen=True, slots=True)
class UpsertMicroSkillInput:
    node_id: str
    subject_code: str
    topic_code: str
    grade: int
    section_code: str
    section_name: str
    micro_skill_name: str
    predecessor_ids: list[str]
    criticality: CriticalityLevel
    source_ref: str | None
    description: str | None
    status: MicroSkillStatus | None
    external_ref: str | None


@dataclass(frozen=True, slots=True)
class LinkMicroSkillPredecessorsInput:
    node_id: str
    predecessor_ids: list[str]


@dataclass(frozen=True, slots=True)
class CreateTestInput:
    subject_code: str
    grade: int
    questions: list[TestQuestionData]


@dataclass(frozen=True, slots=True)
class AssignTestInput:
    test_id: UUID
    child_id: UUID
    retake: bool


@dataclass(frozen=True, slots=True)
class CleanupFixturesInput:
    dry_run: bool
    subject_code_patterns: tuple[str, ...]
    topic_code_patterns: tuple[str, ...]
    node_id_patterns: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ImportContentPayloadInput:
    source_id: str
    contract_version: str
    validate_only: bool
    error_mode: Literal["collect", "fail_fast"]
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ChildScopedInput:
    child_id: UUID


@dataclass(frozen=True, slots=True)
class StartAttemptInput:
    assignment_id: UUID
    child_id: UUID


@dataclass(frozen=True, slots=True)
class SubmitAttemptInput:
    attempt_id: UUID
    answers: list[SubmittedAnswerData]


@dataclass(frozen=True, slots=True)
class SaveAttemptAnswersInput:
    attempt_id: UUID
    answers: list[SubmittedAnswerData]


@dataclass(frozen=True, slots=True)
class AttemptIdInput:
    attempt_id: UUID
