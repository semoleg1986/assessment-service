from dataclasses import dataclass


@dataclass(slots=True)
class DeleteMicroSkillCommand:
    node_id: str
