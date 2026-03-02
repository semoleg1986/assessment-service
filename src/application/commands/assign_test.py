from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class AssignTestCommand:
    test_id: UUID
    child_id: UUID
