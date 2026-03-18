from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class GetChildCorrectionPlanQuery:
    child_id: UUID
