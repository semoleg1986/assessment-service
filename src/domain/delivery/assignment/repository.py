from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.delivery.assignment.entity import AssignmentAggregate


class AssignmentRepository(ABC):
    @abstractmethod
    def save(self, assignment: AssignmentAggregate) -> None: ...

    @abstractmethod
    def get(self, assignment_id: UUID) -> AssignmentAggregate | None: ...

    @abstractmethod
    def list_by_child(self, child_id: UUID) -> list[AssignmentAggregate]: ...
