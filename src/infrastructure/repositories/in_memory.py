from uuid import UUID

from src.domain.content.micro_skill.entity import MicroSkillNode
from src.domain.content.subject.entity import Subject
from src.domain.content.test.aggregate import AssessmentTest
from src.domain.content.topic.entity import Topic
from src.domain.delivery.assignment.aggregate import AssignmentAggregate
from src.domain.delivery.attempt.aggregate import AttemptAggregate
from src.domain.repositories import (
    AssignmentRepository,
    AttemptRepository,
    MicroSkillNodeRepository,
    SubjectRepository,
    TestRepository,
    TopicRepository,
)
from src.domain.shared.statuses import AttemptStatus


class InMemoryTestRepository(TestRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, AssessmentTest] = {}

    def save(self, test: AssessmentTest) -> None:
        self._store[test.test_id] = test

    def get(self, test_id: UUID) -> AssessmentTest | None:
        return self._store.get(test_id)

    def list(self) -> list[AssessmentTest]:
        return list(self._store.values())


class InMemoryAssignmentRepository(AssignmentRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, AssignmentAggregate] = {}

    def save(self, assignment: AssignmentAggregate) -> None:
        self._store[assignment.assignment_id] = assignment

    def get(self, assignment_id: UUID) -> AssignmentAggregate | None:
        return self._store.get(assignment_id)

    def list_by_child(self, child_id: UUID) -> list[AssignmentAggregate]:
        return [a for a in self._store.values() if a.child_id == child_id]


class InMemoryAttemptRepository(AttemptRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, AttemptAggregate] = {}

    def save(self, attempt: AttemptAggregate) -> None:
        self._store[attempt.attempt_id] = attempt

    def get(self, attempt_id: UUID) -> AttemptAggregate | None:
        return self._store.get(attempt_id)

    def find_active_by_assignment(self, assignment_id: UUID) -> AttemptAggregate | None:
        for attempt in self._store.values():
            if (
                attempt.assignment_id == assignment_id
                and attempt.status == AttemptStatus.STARTED
            ):
                return attempt
        return None

    def list_by_child(self, child_id: UUID) -> list[AttemptAggregate]:
        return [a for a in self._store.values() if a.child_id == child_id]


class InMemorySubjectRepository(SubjectRepository):
    def __init__(self) -> None:
        self._store: dict[str, Subject] = {}

    def save(self, subject: Subject) -> None:
        self._store[subject.code] = subject

    def get(self, code: str) -> Subject | None:
        return self._store.get(code)

    def list(self) -> list[Subject]:
        return list(self._store.values())


class InMemoryTopicRepository(TopicRepository):
    def __init__(self) -> None:
        self._store: dict[str, Topic] = {}

    def save(self, topic: Topic) -> None:
        self._store[topic.code] = topic

    def get(self, code: str) -> Topic | None:
        return self._store.get(code)

    def list(self) -> list[Topic]:
        return list(self._store.values())


class InMemoryMicroSkillNodeRepository(MicroSkillNodeRepository):
    def __init__(self) -> None:
        self._store: dict[str, MicroSkillNode] = {}

    def save(self, node: MicroSkillNode) -> None:
        self._store[node.node_id] = node

    def get(self, node_id: str) -> MicroSkillNode | None:
        return self._store.get(node_id)

    def list(self) -> list[MicroSkillNode]:
        return list(self._store.values())

    def delete(self, node_id: str) -> None:
        self._store.pop(node_id, None)
