from dataclasses import dataclass


@dataclass(slots=True)
class LinkMicroSkillPredecessorsCommand:
    node_id: str
    predecessor_ids: list[str]
