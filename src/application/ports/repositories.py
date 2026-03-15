from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.content.micro_skill.entity import MicroSkillNode
from src.domain.content.subject.entity import Subject
from src.domain.content.test.aggregate import AssessmentTest
from src.domain.content.topic.entity import Topic
from src.domain.delivery.assignment.aggregate import AssignmentAggregate
from src.domain.delivery.attempt.aggregate import AttemptAggregate


class TestRepository(ABC):
    @abstractmethod
    def save(self, test: AssessmentTest) -> None: ...

    @abstractmethod
    def get(self, test_id: UUID) -> AssessmentTest | None: ...

    @abstractmethod
    def list(self) -> list[AssessmentTest]: ...


class AssignmentRepository(ABC):
    @abstractmethod
    def save(self, assignment: AssignmentAggregate) -> None: ...

    @abstractmethod
    def get(self, assignment_id: UUID) -> AssignmentAggregate | None: ...

    @abstractmethod
    def list_by_child(self, child_id: UUID) -> list[AssignmentAggregate]: ...


class AttemptRepository(ABC):
    @abstractmethod
    def save(self, attempt: AttemptAggregate) -> None: ...

    @abstractmethod
    def get(self, attempt_id: UUID) -> AttemptAggregate | None: ...

    @abstractmethod
    def find_active_by_assignment(
        self, assignment_id: UUID
    ) -> AttemptAggregate | None: ...

    @abstractmethod
    def list_by_child(self, child_id: UUID) -> list[AttemptAggregate]: ...


class SubjectRepository(ABC):
    @abstractmethod
    def save(self, subject: Subject) -> None: ...

    @abstractmethod
    def get(self, code: str) -> Subject | None: ...

    @abstractmethod
    def list(self) -> list[Subject]: ...


class TopicRepository(ABC):
    @abstractmethod
    def save(self, topic: Topic) -> None: ...

    @abstractmethod
    def get(self, code: str) -> Topic | None: ...

    @abstractmethod
    def list(self) -> list[Topic]: ...


class MicroSkillNodeRepository(ABC):
    @abstractmethod
    def save(self, node: MicroSkillNode) -> None: ...

    @abstractmethod
    def get(self, node_id: str) -> MicroSkillNode | None: ...

    @abstractmethod
    def list(self) -> list[MicroSkillNode]: ...

    @abstractmethod
    def delete(self, node_id: str) -> None: ...
