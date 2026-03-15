from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.delivery.attempt.entity import AttemptAggregate


class AttemptRepository(ABC):
    @abstractmethod
    def save(self, attempt: AttemptAggregate) -> None: ...

    @abstractmethod
    def get(self, attempt_id: UUID) -> AttemptAggregate | None: ...

    @abstractmethod
    def find_active_by_assignment(
        self, assignment_id: UUID
    ) -> AttemptAggregate | None: ...

    @abstractmethod
    def list_by_child(self, child_id: UUID) -> list[AttemptAggregate]: ...
