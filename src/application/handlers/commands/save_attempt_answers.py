from src.application.commands.save_attempt_answers import SaveAttemptAnswersCommand
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.answer import Answer
from src.domain.errors import InvariantViolationError, NotFoundError
from src.domain.value_objects.statuses import AttemptStatus


def handle_save_attempt_answers(
    command: SaveAttemptAnswersCommand,
    uow: UnitOfWork,
) -> dict[str, str | int]:
    attempt = uow.attempts.get(command.attempt_id)
    if attempt is None:
        raise NotFoundError("attempt not found")
    if attempt.status != AttemptStatus.STARTED:
        raise InvariantViolationError(
            "attempt answers can be saved only for started attempt"
        )

    assignment = uow.assignments.get(attempt.assignment_id)
    if assignment is None:
        raise NotFoundError("assignment not found")

    test = uow.tests.get(assignment.test_id)
    if test is None:
        raise NotFoundError("test not found")

    questions_by_id = {q.question_id: q for q in test.questions}
    answers: list[Answer] = []
    for submitted_answer in command.answers:
        if submitted_answer.question_id not in questions_by_id:
            continue
        answers.append(
            Answer(
                question_id=submitted_answer.question_id,
                value=submitted_answer.value,
                selected_option_id=submitted_answer.selected_option_id,
                time_spent_ms=submitted_answer.time_spent_ms,
                is_correct=False,
                awarded_score=0,
            )
        )

    attempt.save_answers(answers)
    uow.attempts.save(attempt)
    uow.commit()

    return {
        "attempt_id": str(command.attempt_id),
        "saved_answers": len(answers),
    }
