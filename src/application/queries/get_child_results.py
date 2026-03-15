from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class GetChildResultsQuery:
    child_id: UUID
