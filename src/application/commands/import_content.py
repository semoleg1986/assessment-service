from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from src.domain.value_objects.questions import (
    DiagnosticTag,
    QuestionType,
    TextMatchMode,
)
from src.domain.value_objects.statuses import CriticalityLevel, MicroSkillStatus


@dataclass(slots=True)
class ImportSubjectInput:
    code: str
    name: str


@dataclass(slots=True)
class ImportTopicInput:
    code: str
    subject_code: str
    grade: int
    name: str


@dataclass(slots=True)
class ImportMicroSkillInput:
    node_id: str
    subject_code: str
    topic_code: str
    grade: int
    section_code: str
    section_name: str
    micro_skill_name: str
    predecessor_ids: list[str] = field(default_factory=list)
    criticality: CriticalityLevel = CriticalityLevel.MEDIUM
    source_ref: str | None = None
    description: str | None = None
    status: MicroSkillStatus = MicroSkillStatus.ACTIVE
    external_ref: str | None = None


@dataclass(slots=True)
class ImportQuestionInput:
    external_id: str
    node_id: str
    text: str
    question_type: QuestionType = QuestionType.TEXT
    answer_key: str | None = None
    correct_option_id: str | None = None
    options: list[ImportQuestionOptionInput] = field(default_factory=list)
    text_distractors: list[ImportTextDistractorInput] = field(default_factory=list)
    max_score: int = 1


@dataclass(slots=True)
class ImportQuestionOptionInput:
    option_id: str
    text: str
    position: int
    diagnostic_tag: DiagnosticTag | None = None


@dataclass(slots=True)
class ImportTextDistractorInput:
    pattern: str
    match_mode: TextMatchMode = TextMatchMode.EXACT
    diagnostic_tag: DiagnosticTag = DiagnosticTag.OTHER


@dataclass(slots=True)
class ImportTestInput:
    external_id: str
    subject_code: str
    grade: int
    questions: list[ImportQuestionInput]


@dataclass(slots=True)
class ImportContentPayloadInput:
    subjects: list[ImportSubjectInput] = field(default_factory=list)
    topics: list[ImportTopicInput] = field(default_factory=list)
    micro_skills: list[ImportMicroSkillInput] = field(default_factory=list)
    tests: list[ImportTestInput] = field(default_factory=list)


@dataclass(slots=True)
class ImportContentCommand:
    source_id: str
    contract_version: str
    payload: ImportContentPayloadInput
    validate_only: bool = False
    error_mode: Literal["collect", "fail_fast"] = "collect"


@dataclass(slots=True)
class ImportContentIssue:
    code: str
    message: str
    path: str


@dataclass(slots=True)
class ImportContentDetails:
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


@dataclass(slots=True)
class ImportContentResult:
    import_id: str
    source_id: str
    imported: int
    status: str
    errors: list[ImportContentIssue] = field(default_factory=list)
    warnings: list[ImportContentIssue] = field(default_factory=list)
    details: ImportContentDetails | None = None
