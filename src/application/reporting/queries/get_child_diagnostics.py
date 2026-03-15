from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class GetChildDiagnosticsQuery:
    child_id: UUID
