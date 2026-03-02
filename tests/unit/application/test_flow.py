from uuid import uuid4

from src.application.commands import (
    AssignTestCommand,
    CreateMicroSkillCommand,
    CreateSubjectCommand,
    CreateTestCommand,
    CreateTopicCommand,
    QuestionInput,
    StartAttemptCommand,
    SubmitAttemptCommand,
    SubmittedAnswerInput,
)
from src.application.handlers import (
    handle_assign_test,
    handle_create_micro_skill,
    handle_create_subject,
    handle_create_test,
    handle_create_topic,
    handle_start_attempt,
    handle_submit_attempt,
)
from src.domain.errors import NotFoundError
from src.domain.value_objects.statuses import CriticalityLevel
from src.infrastructure.uow import InMemoryUnitOfWork


def test_create_assign_start_submit_flow() -> None:
    uow = InMemoryUnitOfWork()
    handle_create_subject(CreateSubjectCommand(code="math", name="Math"), uow=uow)
    handle_create_topic(
        CreateTopicCommand(
            code="M2-S-01", subject_code="math", grade=1, name="Basic addition"
        ),
        uow=uow,
    )
    handle_create_micro_skill(
        CreateMicroSkillCommand(
            node_id="M2-S-01-N1",
            subject_code="math",
            grade=1,
            section_code="R1",
            section_name="Section 1",
            micro_skill_name="Add one-digit numbers",
            predecessor_ids=[],
            criticality=CriticalityLevel.MEDIUM,
        ),
        uow=uow,
    )

    test = handle_create_test(
        CreateTestCommand(
            subject_code="math",
            grade=1,
            questions=[
                QuestionInput(
                    node_id="M2-S-01-N1", text="2+2", answer_key="4", max_score=1
                )
            ],
        ),
        uow=uow,
    )

    assignment = handle_assign_test(
        AssignTestCommand(test_id=test.test_id, child_id=uuid4()),
        uow=uow,
    )

    attempt = handle_start_attempt(
        StartAttemptCommand(
            assignment_id=assignment.assignment_id, child_id=assignment.child_id
        ),
        uow=uow,
    )

    result = handle_submit_attempt(
        SubmitAttemptCommand(
            attempt_id=attempt.attempt_id,
            answers=[
                SubmittedAnswerInput(
                    question_id=test.questions[0].question_id,
                    value="4",
                )
            ],
        ),
        uow=uow,
    )

    assert result["score"] == 1
    assert result["signal"] == "norm"


def test_create_test_fails_when_micro_skill_missing() -> None:
    uow = InMemoryUnitOfWork()
    handle_create_subject(CreateSubjectCommand(code="math", name="Math"), uow=uow)

    try:
        handle_create_test(
            CreateTestCommand(
                subject_code="math",
                grade=1,
                questions=[
                    QuestionInput(
                        node_id="MISSING-NODE",
                        text="2+2",
                        answer_key="4",
                        max_score=1,
                    )
                ],
            ),
            uow=uow,
        )
        assert False, "expected NotFoundError"
    except NotFoundError:
        assert True
