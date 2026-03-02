from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class SubmittedAnswerInput:
    question_id: UUID
    value: str


@dataclass(slots=True)
class SubmitAttemptCommand:
    attempt_id: UUID
    answers: list[SubmittedAnswerInput]
