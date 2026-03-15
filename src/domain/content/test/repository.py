from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.content.test.entity import AssessmentTest


class TestRepository(ABC):
    @abstractmethod
    def save(self, test: AssessmentTest) -> None: ...

    @abstractmethod
    def get(self, test_id: UUID) -> AssessmentTest | None: ...

    @abstractmethod
    def list(self) -> list[AssessmentTest]: ...
