from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class GetChildSkillResultsQuery:
    child_id: UUID
