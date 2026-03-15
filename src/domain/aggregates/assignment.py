from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from src.domain.value_objects.statuses import AssignmentStatus


@dataclass(slots=True)
class AssignmentAggregate:
    """
    Назначение теста конкретному ребёнку.

    :param assignment_id: Идентификатор назначения.
    :type assignment_id: UUID
    :param test_id: Идентификатор теста.
    :type test_id: UUID
    :param child_id: Идентификатор ребёнка.
    :type child_id: UUID
    :param status: Текущий статус назначения.
    :type status: AssignmentStatus
    :param assigned_at: Время назначения.
    :type assigned_at: datetime
    :param version: Версия агрегата.
    :type version: int
    :param attempt_no: Порядковый номер попытки по тесту для ребёнка.
    :type attempt_no: int
    """

    assignment_id: UUID
    test_id: UUID
    child_id: UUID
    status: AssignmentStatus = AssignmentStatus.ASSIGNED
    assigned_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: int = 1
    attempt_no: int = 1

    def __post_init__(self) -> None:
        if self.attempt_no < 1:
            raise ValueError("attempt_no must be >= 1")

    def mark_started(self) -> None:
        """Перевести назначение в статус `started`."""
        self.status = AssignmentStatus.STARTED
        self.version += 1

    def mark_completed(self) -> None:
        """Перевести назначение в статус `completed`."""
        self.status = AssignmentStatus.COMPLETED
        self.version += 1
