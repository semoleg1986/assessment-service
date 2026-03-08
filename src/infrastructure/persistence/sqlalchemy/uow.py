from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from src.application.ports.unit_of_work import UnitOfWork
from src.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyAssignmentRepository,
    SqlAlchemyAttemptRepository,
    SqlAlchemyMicroSkillNodeRepository,
    SqlAlchemySubjectRepository,
    SqlAlchemyTestRepository,
    SqlAlchemyTopicRepository,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url, future=True)
        self._session_factory = scoped_session(
            sessionmaker(
                bind=self._engine,
                autoflush=False,
                autocommit=False,
                expire_on_commit=False,
            )
        )
        self.tests = SqlAlchemyTestRepository(self._session_factory)
        self.assignments = SqlAlchemyAssignmentRepository(self._session_factory)
        self.attempts = SqlAlchemyAttemptRepository(self._session_factory)
        self.subjects = SqlAlchemySubjectRepository(self._session_factory)
        self.topics = SqlAlchemyTopicRepository(self._session_factory)
        self.micro_skills = SqlAlchemyMicroSkillNodeRepository(self._session_factory)

    def commit(self) -> None:
        self._session_factory.commit()

    def close(self) -> None:
        self._session_factory.remove()
