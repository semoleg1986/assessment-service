from __future__ import annotations

from uuid import UUID

from src.application.facade import (
    AttemptIdInput,
    SaveAttemptAnswersInput,
    StartAttemptInput,
    SubmitAttemptInput,
    SubmittedAnswerData,
)
from src.interface.http.v1.schemas import (
    SaveAttemptAnswersRequest,
    StartAttemptRequest,
    SubmitAttemptRequest,
)


def to_start_attempt_input(body: StartAttemptRequest) -> StartAttemptInput:
    return StartAttemptInput(
        assignment_id=body.assignment_id,
        child_id=body.child_id,
    )


def to_submit_attempt_input(
    *, attempt_id: UUID, body: SubmitAttemptRequest
) -> SubmitAttemptInput:
    return SubmitAttemptInput(
        attempt_id=attempt_id,
        answers=[
            SubmittedAnswerData(
                question_id=item.question_id,
                value=item.value,
                selected_option_id=item.selected_option_id,
                time_spent_ms=item.time_spent_ms,
            )
            for item in body.answers
        ],
    )


def to_save_attempt_answers_input(
    *, attempt_id: UUID, body: SaveAttemptAnswersRequest
) -> SaveAttemptAnswersInput:
    return SaveAttemptAnswersInput(
        attempt_id=attempt_id,
        answers=[
            SubmittedAnswerData(
                question_id=item.question_id,
                value=item.value,
                selected_option_id=item.selected_option_id,
                time_spent_ms=item.time_spent_ms,
            )
            for item in body.answers
        ],
    )


def to_attempt_id_input(*, attempt_id: UUID) -> AttemptIdInput:
    return AttemptIdInput(attempt_id=attempt_id)
