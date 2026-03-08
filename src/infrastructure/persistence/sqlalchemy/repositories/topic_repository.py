from __future__ import annotations

from sqlalchemy import select

from src.application.ports.repositories import TopicRepository
from src.domain.entities.topic import Topic
from src.infrastructure.persistence.sqlalchemy.mappers import topic_from_model
from src.infrastructure.persistence.sqlalchemy.models import TopicModel
from src.infrastructure.persistence.sqlalchemy.session_types import SessionLike


class SqlAlchemyTopicRepository(TopicRepository):
    def __init__(self, session: SessionLike) -> None:
        self._session = session

    def save(self, topic: Topic) -> None:
        model = self._session.get(TopicModel, topic.code)
        if model is None:
            model = TopicModel(
                code=topic.code,
                subject_code=topic.subject_code,
                grade=topic.grade,
                name=topic.name,
            )
            self._session.add(model)
            return

        model.subject_code = topic.subject_code
        model.grade = topic.grade
        model.name = topic.name

    def get(self, code: str) -> Topic | None:
        model = self._session.get(TopicModel, code)
        if model is None:
            return None
        return topic_from_model(model)

    def list(self) -> list[Topic]:
        rows = self._session.scalars(select(TopicModel).order_by(TopicModel.code)).all()
        return [topic_from_model(r) for r in rows]
