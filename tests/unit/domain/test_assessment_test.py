from uuid import uuid4

import pytest

from src.domain.content.test.aggregate import AssessmentTest
from src.domain.content.test.entities.question import Question
from src.domain.errors import InvariantViolationError


def test_revise_updates_content_and_increments_version() -> None:
    initial_question = Question(
        question_id=uuid4(),
        node_id="node-1",
        text="1 + 1 = ?",
        answer_key="2",
        max_score=1,
    )
    test = AssessmentTest(
        test_id=uuid4(),
        subject_code="math",
        grade=2,
        questions=[initial_question],
        version=3,
    )

    updated_question = Question(
        question_id=uuid4(),
        node_id="node-2",
        text="2 + 2 = ?",
        answer_key="4",
        max_score=1,
    )
    test.revise(subject_code="math", grade=3, questions=[updated_question])

    assert test.grade == 3
    assert test.questions == [updated_question]
    assert test.version == 4


def test_revise_checks_invariants() -> None:
    initial_question = Question(
        question_id=uuid4(),
        node_id="node-1",
        text="1 + 1 = ?",
        answer_key="2",
        max_score=1,
    )
    test = AssessmentTest(
        test_id=uuid4(),
        subject_code="math",
        grade=2,
        questions=[initial_question],
    )

    with pytest.raises(InvariantViolationError, match=r"grade must be in \[1\.\.4\]"):
        test.revise(subject_code="math", grade=5, questions=[initial_question])
