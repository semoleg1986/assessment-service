from __future__ import annotations

from src.application.facade import (
    AssessmentUserFacade,
    AttemptIdInput,
    ChildScopedInput,
    SaveAttemptAnswersInput,
    StartAttemptInput,
    SubmitAttemptInput,
    SubmittedAnswerData,
)
from src.infrastructure.uow import InMemoryUnitOfWork

from .support import build_content_facade, seed_basic_catalog


def test_user_facade_contract() -> None:
    uow = InMemoryUnitOfWork()
    content = build_content_facade(uow)
    assignment_id, child_id = seed_basic_catalog(content)

    user = AssessmentUserFacade(uow=uow)

    assignments = user.list_assignments_by_child(
        payload=ChildScopedInput(child_id=child_id)
    )
    assert len(assignments) == 1

    attempt = user.start_attempt(
        payload=StartAttemptInput(assignment_id=assignment_id, child_id=child_id)
    )
    save_result = user.save_attempt_answers(
        payload=SaveAttemptAnswersInput(
            attempt_id=attempt.attempt_id,
            answers=[
                SubmittedAnswerData(
                    question_id=content.list_tests()[0].questions[0].question_id,
                    value="4",
                    selected_option_id=None,
                    time_spent_ms=1200,
                )
            ],
        )
    )
    assert int(save_result["saved_answers"]) == 1

    submit = user.submit_attempt(
        payload=SubmitAttemptInput(
            attempt_id=attempt.attempt_id,
            answers=[
                SubmittedAnswerData(
                    question_id=content.list_tests()[0].questions[0].question_id,
                    value="4",
                    selected_option_id=None,
                    time_spent_ms=1200,
                )
            ],
        )
    )
    assert submit["score"] == 1

    attempt_result = user.get_attempt_result(
        payload=AttemptIdInput(attempt_id=attempt.attempt_id)
    )
    assert attempt_result["status"] == "submitted"
    assert len(attempt_result["answers"]) == 1
