from src.application.ports.unit_of_work import UnitOfWork
from src.application.reporting.queries.get_child_diagnostics import (
    GetChildDiagnosticsQuery,
)


def handle_get_child_diagnostics(
    query: GetChildDiagnosticsQuery,
    *,
    uow: UnitOfWork,
) -> dict[str, int]:
    return {
        "assignments_total": len(uow.assignments.list_by_child(query.child_id)),
        "attempts_total": len(uow.attempts.list_by_child(query.child_id)),
    }
