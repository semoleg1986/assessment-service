from abc import ABC, abstractmethod

from src.domain.content.subject.entity import Subject


class SubjectRepository(ABC):
    @abstractmethod
    def save(self, subject: Subject) -> None: ...

    @abstractmethod
    def get(self, code: str) -> Subject | None: ...

    @abstractmethod
    def list(self) -> list[Subject]: ...
