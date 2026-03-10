from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class GetTestByIdQuery:
    test_id: UUID
