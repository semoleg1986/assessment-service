from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class StartAttemptCommand:
    assignment_id: UUID
    child_id: UUID
