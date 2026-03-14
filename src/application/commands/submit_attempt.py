from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class SubmittedAnswerInput:
    question_id: UUID
    value: str | None = None
    selected_option_id: str | None = None


@dataclass(slots=True)
class SubmitAttemptCommand:
    attempt_id: UUID
    answers: list[SubmittedAnswerInput]
