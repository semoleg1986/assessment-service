from abc import ABC, abstractmethod

from src.domain.content.micro_skill.repository import MicroSkillNodeRepository
from src.domain.content.subject.repository import SubjectRepository
from src.domain.content.test.repository import TestRepository
from src.domain.content.topic.repository import TopicRepository
from src.domain.delivery.assignment.repository import AssignmentRepository
from src.domain.delivery.attempt.repository import AttemptRepository


class UnitOfWork(ABC):
    tests: TestRepository
    assignments: AssignmentRepository
    attempts: AttemptRepository
    subjects: SubjectRepository
    topics: TopicRepository
    micro_skills: MicroSkillNodeRepository

    @abstractmethod
    def commit(self) -> None: ...
