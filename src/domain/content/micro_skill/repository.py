from abc import ABC, abstractmethod

from src.domain.content.micro_skill.entity import MicroSkillNode


class MicroSkillNodeRepository(ABC):
    @abstractmethod
    def save(self, node: MicroSkillNode) -> None: ...

    @abstractmethod
    def get(self, node_id: str) -> MicroSkillNode | None: ...

    @abstractmethod
    def list(self) -> list[MicroSkillNode]: ...

    @abstractmethod
    def delete(self, node_id: str) -> None: ...
