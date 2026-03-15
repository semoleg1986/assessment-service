from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class GetAttemptResultQuery:
    attempt_id: UUID
