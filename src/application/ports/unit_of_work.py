from abc import ABC, abstractmethod

from src.domain.repositories import (
    AssignmentRepository,
    AttemptRepository,
    MicroSkillNodeRepository,
    SubjectRepository,
    TestRepository,
    TopicRepository,
)


class UnitOfWork(ABC):
    tests: TestRepository
    assignments: AssignmentRepository
    attempts: AttemptRepository
    subjects: SubjectRepository
    topics: TopicRepository
    micro_skills: MicroSkillNodeRepository

    @abstractmethod
    def commit(self) -> None: ...
