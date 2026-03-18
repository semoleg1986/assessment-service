from __future__ import annotations

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
        answers: list[SubmittedAnswerInput],
    ) -> SubmitAttemptResult:
        return handle_submit_attempt(
            SubmitAttemptCommand(attempt_id=attempt_id, answers=answers),
            uow=self._uow,
        )

    def save_attempt_answers(
        self,
        *,
        attempt_id: UUID,
        answers: list[SubmittedAnswerInput],
    ) -> dict[str, str | int]:
        return handle_save_attempt_answers(
            SaveAttemptAnswersCommand(attempt_id=attempt_id, answers=answers),
            uow=self._uow,
        )

    def get_attempt_result(self, *, attempt_id: UUID) -> AttemptResult:
        return handle_get_attempt_result(
            GetAttemptResultQuery(attempt_id=attempt_id),
            uow=self._uow,
        )
