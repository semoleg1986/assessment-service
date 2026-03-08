from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from src.application.ports.repositories import AttemptRepository
from src.domain.aggregates.attempt import AttemptAggregate
from src.domain.value_objects.statuses import AttemptStatus
from src.infrastructure.persistence.sqlalchemy.mappers import attempt_from_model
from src.infrastructure.persistence.sqlalchemy.models import AnswerModel, AttemptModel
from src.infrastructure.persistence.sqlalchemy.session_types import SessionLike


class SqlAlchemyAttemptRepository(AttemptRepository):
    def __init__(self, session: SessionLike) -> None:
        self._session = session

    def save(self, attempt: AttemptAggregate) -> None:
        model = self._session.get(AttemptModel, attempt.attempt_id)
        if model is None:
            model = AttemptModel(
                attempt_id=attempt.attempt_id,
                assignment_id=attempt.assignment_id,
                child_id=attempt.child_id,
                status=attempt.status.value,
                started_at=attempt.started_at,
                submitted_at=attempt.submitted_at,
                score=attempt.score,
                version=attempt.version,
            )
            self._session.add(model)
        else:
            model.assignment_id = attempt.assignment_id
            model.child_id = attempt.child_id
            model.status = attempt.status.value
            model.started_at = attempt.started_at
            model.submitted_at = attempt.submitted_at
            model.score = attempt.score
            model.version = attempt.version

        self._session.query(AnswerModel).filter(
            AnswerModel.attempt_id == attempt.attempt_id
        ).delete(synchronize_session=False)
        for answer in attempt.answers:
            self._session.add(
                AnswerModel(
                    attempt_id=attempt.attempt_id,
                    question_id=answer.question_id,
                    value=answer.value,
                    is_correct=answer.is_correct,
                    awarded_score=answer.awarded_score,
                )
            )

    def get(self, attempt_id: UUID) -> AttemptAggregate | None:
        model = self._session.get(AttemptModel, attempt_id)
        if model is None:
            return None
        return attempt_from_model(model)

    def find_active_by_assignment(self, assignment_id: UUID) -> AttemptAggregate | None:
        model = self._session.scalars(
            select(AttemptModel).where(
                AttemptModel.assignment_id == assignment_id,
                AttemptModel.status == AttemptStatus.STARTED.value,
            )
        ).first()
        if model is None:
            return None
        return attempt_from_model(model)

    def list_by_child(self, child_id: UUID) -> list[AttemptAggregate]:
        rows = self._session.scalars(
            select(AttemptModel)
            .where(AttemptModel.child_id == child_id)
            .order_by(AttemptModel.started_at)
        ).all()
        return [attempt_from_model(row) for row in rows]
