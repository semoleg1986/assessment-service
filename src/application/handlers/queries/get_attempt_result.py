from typing import TypedDict

from src.application.ports.unit_of_work import UnitOfWork
from src.application.queries.get_attempt_result import GetAttemptResultQuery
from src.domain.errors import NotFoundError


class AttemptAnswerResult(TypedDict):
    question_id: str
    value: str
    is_correct: bool
    awarded_score: int


class AttemptResult(TypedDict):
    attempt_id: str
    status: str
    score: int
    answers: list[AttemptAnswerResult]


def handle_get_attempt_result(
    query: GetAttemptResultQuery, uow: UnitOfWork
) -> AttemptResult:
    """
    Получить сохранённый результат попытки.

    :param query: Запрос результата попытки.
    :type query: GetAttemptResultQuery
    :param uow: Unit of Work.
    :type uow: UnitOfWork
    :return: Данные результата попытки.
    :rtype: AttemptResult
    """
    attempt = uow.attempts.get(query.attempt_id)
    if attempt is None:
        raise NotFoundError("attempt not found")
    return {
        "attempt_id": str(attempt.attempt_id),
        "status": attempt.status.value,
        "score": attempt.score,
        "answers": [
            {
                "question_id": str(a.question_id),
                "value": a.value,
                "is_correct": a.is_correct,
                "awarded_score": a.awarded_score,
            }
            for a in attempt.answers
        ],
    }
