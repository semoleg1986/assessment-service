from typing import TypedDict

from src.application.commands.submit_attempt import SubmitAttemptCommand
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.answer import Answer
from src.domain.errors import NotFoundError
from src.domain.value_objects.statuses import AttemptStatus


class SubmitAttemptResult(TypedDict):
    attempt_id: str
    status: str
    score: int
    max_score: int
    signal: str


def handle_submit_attempt(
    command: SubmitAttemptCommand, uow: UnitOfWork
) -> SubmitAttemptResult:
    """
    Завершить попытку, оценить ответы и вернуть результат.

    :param command: Команда отправки попытки.
    :type command: SubmitAttemptCommand
    :param uow: Unit of Work.
    :type uow: UnitOfWork
    :return: Результат отправки (балл и сигнал).
    :rtype: SubmitAttemptResult
    """
    attempt = uow.attempts.get(command.attempt_id)
    if attempt is None:
        raise NotFoundError("attempt not found")

    assignment = uow.assignments.get(attempt.assignment_id)
    if assignment is None:
        raise NotFoundError("assignment not found")

    test = uow.tests.get(assignment.test_id)
    if test is None:
        raise NotFoundError("test not found")

    by_id = {q.question_id: q for q in test.questions}
    answers = []
    for a in command.answers:
        q = by_id.get(a.question_id)
        if q is None:
            continue
        is_correct = a.value.strip() == q.answer_key.strip()
        answers.append(
            Answer(
                question_id=a.question_id,
                value=a.value,
                is_correct=is_correct,
                awarded_score=q.max_score if is_correct else 0,
            )
        )

    attempt.submit(answers)
    assignment.mark_completed()

    uow.attempts.save(attempt)
    uow.assignments.save(assignment)
    uow.commit()

    max_score = sum(q.max_score for q in test.questions)
    ratio = attempt.score / max_score if max_score else 0
    if ratio >= 0.85:
        signal = "norm"
    elif ratio >= 0.70:
        signal = "risk"
    elif ratio >= 0.50:
        signal = "gap"
    else:
        signal = "critical_gap"

    return {
        "attempt_id": str(attempt.attempt_id),
        "status": AttemptStatus.SUBMITTED.value,
        "score": attempt.score,
        "max_score": max_score,
        "signal": signal,
    }
