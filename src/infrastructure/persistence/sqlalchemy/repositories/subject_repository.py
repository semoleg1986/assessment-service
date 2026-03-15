from __future__ import annotations

from sqlalchemy import select

from src.domain.content.subject.entity import Subject
from src.domain.repositories import SubjectRepository
from src.infrastructure.persistence.sqlalchemy.mappers import subject_from_model
from src.infrastructure.persistence.sqlalchemy.models import SubjectModel
from src.infrastructure.persistence.sqlalchemy.session_types import SessionLike


class SqlAlchemySubjectRepository(SubjectRepository):
    def __init__(self, session: SessionLike) -> None:
        self._session = session

    def save(self, subject: Subject) -> None:
        model = self._session.get(SubjectModel, subject.code)
        if model is None:
            self._session.add(SubjectModel(code=subject.code, name=subject.name))
            return
        model.name = subject.name

    def get(self, code: str) -> Subject | None:
        model = self._session.get(SubjectModel, code)
        if model is None:
            return None
        return subject_from_model(model)

    def list(self) -> list[Subject]:
        rows = self._session.scalars(
            select(SubjectModel).order_by(SubjectModel.code)
        ).all()
        return [subject_from_model(r) for r in rows]
