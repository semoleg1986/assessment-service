from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from src.domain.delivery.assignment.aggregate import AssignmentAggregate
from src.domain.repositories import AssignmentRepository
from src.infrastructure.persistence.sqlalchemy.mappers import assignment_from_model
from src.infrastructure.persistence.sqlalchemy.models import AssignmentModel
from src.infrastructure.persistence.sqlalchemy.session_types import SessionLike


class SqlAlchemyAssignmentRepository(AssignmentRepository):
    def __init__(self, session: SessionLike) -> None:
        self._session = session

    def save(self, assignment: AssignmentAggregate) -> None:
        model = self._session.get(AssignmentModel, assignment.assignment_id)
        if model is None:
            model = AssignmentModel(
                assignment_id=assignment.assignment_id,
                test_id=assignment.test_id,
                child_id=assignment.child_id,
                status=assignment.status.value,
                assigned_at=assignment.assigned_at,
                version=assignment.version,
                attempt_no=assignment.attempt_no,
            )
            self._session.add(model)
            return

        model.test_id = assignment.test_id
        model.child_id = assignment.child_id
        model.status = assignment.status.value
        model.assigned_at = assignment.assigned_at
        model.version = assignment.version
        model.attempt_no = assignment.attempt_no

    def get(self, assignment_id: UUID) -> AssignmentAggregate | None:
        model = self._session.get(AssignmentModel, assignment_id)
        if model is None:
            return None
        return assignment_from_model(model)

    def list_by_child(self, child_id: UUID) -> list[AssignmentAggregate]:
        rows = self._session.scalars(
            select(AssignmentModel)
            .where(AssignmentModel.child_id == child_id)
            .order_by(AssignmentModel.assigned_at)
        ).all()
        return [assignment_from_model(r) for r in rows]
