from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.shared.questions import DiagnosticTag, QuestionType, TextMatchMode


@dataclass(slots=True)
class QuestionOptionInput:
    option_id: str
    text: str
    position: int
    diagnostic_tag: DiagnosticTag | None = None


@dataclass(slots=True)
class TextDistractorInput:
    pattern: str
    match_mode: TextMatchMode = TextMatchMode.EXACT
    diagnostic_tag: DiagnosticTag = DiagnosticTag.OTHER


@dataclass(slots=True)
class QuestionInput:
    node_id: str
    text: str
    question_type: QuestionType = QuestionType.TEXT
    answer_key: str | None = None
    correct_option_id: str | None = None
    options: list[QuestionOptionInput] = field(default_factory=list)
    text_distractors: list[TextDistractorInput] = field(default_factory=list)
    max_score: int = 1


@dataclass(slots=True)
class CreateTestCommand:
    subject_code: str
    grade: int
    questions: list[QuestionInput]
