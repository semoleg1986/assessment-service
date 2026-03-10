from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class ListAssignmentsByChildQuery:
    child_id: UUID
