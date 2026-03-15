from dataclasses import dataclass
from uuid import UUID

from src.application.delivery.commands.submit_attempt import SubmittedAnswerInput


@dataclass(slots=True)
class SaveAttemptAnswersCommand:
    attempt_id: UUID
    answers: list[SubmittedAnswerInput]
