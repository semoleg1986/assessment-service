from uuid import uuid4

import pytest

from src.domain.delivery.attempt.aggregate import AttemptAggregate
from src.domain.delivery.attempt.entities.answer import Answer
from src.domain.errors import InvariantViolationError


def test_submit_attempt_changes_status_and_score() -> None:
    attempt = AttemptAggregate(
        attempt_id=uuid4(), assignment_id=uuid4(), child_id=uuid4()
    )
    attempt.submit(
        [
            Answer(question_id=uuid4(), value="1", is_correct=True, awarded_score=1),
            Answer(question_id=uuid4(), value="2", is_correct=False, awarded_score=0),
        ]
    )

    assert attempt.status.value == "submitted"
    assert attempt.score == 1
    assert attempt.submitted_at is not None


def test_submit_attempt_twice_forbidden() -> None:
    attempt = AttemptAggregate(
        attempt_id=uuid4(), assignment_id=uuid4(), child_id=uuid4()
    )
    attempt.submit(
        [Answer(question_id=uuid4(), value="1", is_correct=True, awarded_score=1)]
    )

    with pytest.raises(InvariantViolationError):
        attempt.submit([])
