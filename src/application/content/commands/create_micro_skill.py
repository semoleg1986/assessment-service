from dataclasses import dataclass

from src.domain.shared.statuses import CriticalityLevel, MicroSkillStatus


@dataclass(slots=True)
class CreateMicroSkillCommand:
    node_id: str
    subject_code: str
    topic_code: str
    grade: int
    section_code: str
    section_name: str
    micro_skill_name: str
    predecessor_ids: list[str]
    criticality: CriticalityLevel
    source_ref: str | None = None
    description: str | None = None
    status: MicroSkillStatus = MicroSkillStatus.ACTIVE
    external_ref: str | None = None
