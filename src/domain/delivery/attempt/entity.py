from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from src.domain.delivery.attempt.answer import Answer
from src.domain.errors import InvariantViolationError
from src.domain.shared.statuses import AttemptStatus


@dataclass(slots=True)
class AttemptAggregate:
    """
    Попытка прохождения теста по назначению.

    :param attempt_id: Идентификатор попытки.
    :type attempt_id: UUID
    :param assignment_id: Идентификатор назначения.
    :type assignment_id: UUID
    :param child_id: Идентификатор ребёнка.
    :type child_id: UUID
    :param status: Статус попытки.
    :type status: AttemptStatus
    :param started_at: Время старта попытки.
    :type started_at: datetime
    :param submitted_at: Время отправки попытки.
    :type submitted_at: datetime | None
    :param score: Итоговый балл попытки.
    :type score: int
    :param answers: Ответы ученика.
    :type answers: list[Answer]
    :param version: Версия агрегата.
    :type version: int
    """

    attempt_id: UUID
    assignment_id: UUID
    child_id: UUID
    status: AttemptStatus = AttemptStatus.STARTED
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    submitted_at: datetime | None = None
    score: int = 0
    answers: list[Answer] = field(default_factory=list)
    version: int = 1

    def save_answers(self, answers: list[Answer]) -> None:
        """
        Сохранить черновик ответов без завершения попытки.

        :param answers: Текущие ответы ученика.
        :type answers: list[Answer]
        """
        if self.status != AttemptStatus.STARTED:
            raise InvariantViolationError(
                "attempt answers can be saved only for started attempt"
            )
        self.answers = answers
        self.version += 1

    def submit(self, answers: list[Answer]) -> None:
        """
        Завершить попытку и зафиксировать ответы.

        :param answers: Ответы ученика.
        :type answers: list[Answer]
        """
        if self.status != AttemptStatus.STARTED:
            raise InvariantViolationError("attempt can be submitted only from started")
        self.answers = answers
        self.score = sum(a.awarded_score for a in answers)
        self.status = AttemptStatus.SUBMITTED
        self.submitted_at = datetime.now(UTC)
        self.version += 1
