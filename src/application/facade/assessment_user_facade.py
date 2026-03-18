from __future__ import annotations

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
from src.application.facade.inputs import (
    AttemptIdInput,
    ChildScopedInput,
    SaveAttemptAnswersInput,
    StartAttemptInput,
    SubmitAttemptInput,
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
        self, *, payload: ChildScopedInput
    ) -> list[AssignmentAggregate]:
        return handle_list_assignments_by_child(
            ListAssignmentsByChildQuery(child_id=payload.child_id),
            uow=self._uow,
        )

    def start_attempt(self, *, payload: StartAttemptInput) -> AttemptAggregate:
        return handle_start_attempt(
            StartAttemptCommand(
                assignment_id=payload.assignment_id,
                child_id=payload.child_id,
            ),
            uow=self._uow,
        )

    def submit_attempt(
        self,
        *,
        payload: SubmitAttemptInput,
    ) -> SubmitAttemptResult:
        submitted_answers = [
            SubmittedAnswerInput(
                question_id=item.question_id,
                value=item.value,
                selected_option_id=item.selected_option_id,
                time_spent_ms=item.time_spent_ms,
            )
            for item in payload.answers
        ]
        return handle_submit_attempt(
            SubmitAttemptCommand(
                attempt_id=payload.attempt_id, answers=submitted_answers
            ),
            uow=self._uow,
        )

    def save_attempt_answers(
        self,
        *,
        payload: SaveAttemptAnswersInput,
    ) -> dict[str, str | int]:
        submitted_answers = [
            SubmittedAnswerInput(
                question_id=item.question_id,
                value=item.value,
                selected_option_id=item.selected_option_id,
                time_spent_ms=item.time_spent_ms,
            )
            for item in payload.answers
        ]
        return handle_save_attempt_answers(
            SaveAttemptAnswersCommand(
                attempt_id=payload.attempt_id, answers=submitted_answers
            ),
            uow=self._uow,
        )

    def get_attempt_result(self, *, payload: AttemptIdInput) -> AttemptResult:
        return handle_get_attempt_result(
            GetAttemptResultQuery(attempt_id=payload.attempt_id),
            uow=self._uow,
        )
