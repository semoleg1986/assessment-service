from __future__ import annotations

from dataclasses import dataclass
from os import getenv

from src.application.ports.unit_of_work import UnitOfWork
from src.infrastructure.persistence.sqlalchemy.uow import SqlAlchemyUnitOfWork
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


@dataclass(frozen=True)
class AppSettings:
    database_url: str | None

    @classmethod
    def from_env(cls) -> "AppSettings":
        url = getenv("DATABASE_URL", "").strip()
        return cls(database_url=url or None)


_in_memory_uow = InMemoryUnitOfWork()


def build_uow() -> UnitOfWork:
    settings = AppSettings.from_env()
    if settings.database_url:
        return SqlAlchemyUnitOfWork(settings.database_url)
    return _in_memory_uow
