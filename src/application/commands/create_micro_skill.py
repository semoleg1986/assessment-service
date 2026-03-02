from dataclasses import dataclass

from src.domain.value_objects.statuses import CriticalityLevel


@dataclass(slots=True)
class CreateMicroSkillCommand:
    node_id: str
    subject_code: str
    grade: int
    section_code: str
    section_name: str
    micro_skill_name: str
    predecessor_ids: list[str]
    criticality: CriticalityLevel
    source_ref: str | None = None
