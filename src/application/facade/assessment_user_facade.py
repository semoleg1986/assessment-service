from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.application.delivery.commands.save_attempt_answers import (
    SaveAttemptAnswersCommand,
)
from src.application.delivery.commands.start_attempt import StartAttemptCommand
from src.application.delivery.commands.submit_attempt import (
    SubmitAttemptCommand,
    SubmittedAnswerInput,
)
from src.application.delivery.handlers.get_attempt_result import (
    AttemptResult,
    handle_get_attempt_result,
)
from src.application.delivery.handlers.list_assignments_by_child import (
    handle_list_assignments_by_child,
)
from src.application.delivery.handlers.save_attempt_answers import (
    handle_save_attempt_answers,
)
from src.application.delivery.handlers.start_attempt import handle_start_attempt
from src.application.delivery.handlers.submit_attempt import handle_submit_attempt
from src.application.delivery.handlers.submit_attempt import SubmitAttemptResult
from src.application.delivery.queries.get_attempt_result import GetAttemptResultQuery
from src.application.delivery.queries.list_assignments_by_child import (
    ListAssignmentsByChildQuery,
)
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.delivery.assignment.entity import AssignmentAggregate
from src.domain.delivery.attempt.entity import AttemptAggregate


@dataclass(frozen=True, slots=True)
class SubmittedAnswerData:
    question_id: UUID
    value: str | None
    selected_option_id: str | None
    time_spent_ms: int | None


class AssessmentUserFacade:
    """
    Фасад application-слоя для user сценариев assessment-service.
    """

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def list_assignments_by_child(
        self, *, child_id: UUID
    ) -> list[AssignmentAggregate]:
        return handle_list_assignments_by_child(
            ListAssignmentsByChildQuery(child_id=child_id),
            uow=self._uow,
        )

    def start_attempt(
        self, *, assignment_id: UUID, child_id: UUID
    ) -> AttemptAggregate:
        return handle_start_attempt(
            StartAttemptCommand(assignment_id=assignment_id, child_id=child_id),
            uow=self._uow,
        )

    def submit_attempt(
        self,
        *,
        attempt_id: UUID,
        answers: list[SubmittedAnswerData],
    ) -> SubmitAttemptResult:
        submitted_answers = [
            SubmittedAnswerInput(
                question_id=item.question_id,
                value=item.value,
                selected_option_id=item.selected_option_id,
                time_spent_ms=item.time_spent_ms,
            )
            for item in answers
        ]
        return handle_submit_attempt(
            SubmitAttemptCommand(attempt_id=attempt_id, answers=submitted_answers),
            uow=self._uow,
        )

    def save_attempt_answers(
        self,
        *,
        attempt_id: UUID,
        answers: list[SubmittedAnswerData],
    ) -> dict[str, str | int]:
        submitted_answers = [
            SubmittedAnswerInput(
                question_id=item.question_id,
                value=item.value,
                selected_option_id=item.selected_option_id,
                time_spent_ms=item.time_spent_ms,
            )
            for item in answers
        ]
        return handle_save_attempt_answers(
            SaveAttemptAnswersCommand(attempt_id=attempt_id, answers=submitted_answers),
            uow=self._uow,
        )

    def get_attempt_result(self, *, attempt_id: UUID) -> AttemptResult:
        return handle_get_attempt_result(
            GetAttemptResultQuery(attempt_id=attempt_id),
            uow=self._uow,
        )
