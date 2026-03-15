from src.application.delivery.queries.list_assignments_by_child import (
    ListAssignmentsByChildQuery,
)
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.delivery.assignment.entity import AssignmentAggregate


def handle_list_assignments_by_child(
    query: ListAssignmentsByChildQuery,
    *,
    uow: UnitOfWork,
) -> list[AssignmentAggregate]:
    return uow.assignments.list_by_child(query.child_id)
