from src.application.ports.unit_of_work import UnitOfWork
from src.infrastructure.repositories.in_memory import (
    InMemoryAssignmentRepository,
    InMemoryAttemptRepository,
    InMemoryMicroSkillNodeRepository,
    InMemorySubjectRepository,
    InMemoryTestRepository,
    InMemoryTopicRepository,
)


class InMemoryUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.tests = InMemoryTestRepository()
        self.assignments = InMemoryAssignmentRepository()
        self.attempts = InMemoryAttemptRepository()
        self.subjects = InMemorySubjectRepository()
        self.topics = InMemoryTopicRepository()
        self.micro_skills = InMemoryMicroSkillNodeRepository()

    def commit(self) -> None:
        return None
