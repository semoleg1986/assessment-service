from __future__ import annotations

from src.application.facade import (
    AssessmentResultsFacade,
    AssessmentUserFacade,
    ChildScopedInput,
    StartAttemptInput,
    SubmitAttemptInput,
    SubmittedAnswerData,
)
from src.infrastructure.uow import InMemoryUnitOfWork

from .support import build_content_facade, seed_basic_catalog


def test_results_facade_contract() -> None:
    uow = InMemoryUnitOfWork()
    content = build_content_facade(uow)
    assignment_id, child_id = seed_basic_catalog(content)

    user = AssessmentUserFacade(uow=uow)
    results = AssessmentResultsFacade(uow=uow)

    attempt = user.start_attempt(
        payload=StartAttemptInput(assignment_id=assignment_id, child_id=child_id)
    )
    user.submit_attempt(
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

    child_results = results.get_child_results(
        payload=ChildScopedInput(child_id=child_id)
    )
    assert child_results["summary"]["attempts_total"] == 1
    assert child_results["summary"]["correct_answers_total"] == 1

    diagnostics = results.get_child_diagnostics(
        payload=ChildScopedInput(child_id=child_id)
    )
    assert diagnostics["attempts_total"] == 1

    skill_results = results.get_child_skill_results(
        payload=ChildScopedInput(child_id=child_id)
    )
    assert skill_results["summary"]["total_skills"] >= 1
