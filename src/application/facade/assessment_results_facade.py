from __future__ import annotations

from uuid import UUID

from src.application.ports.unit_of_work import UnitOfWork
from src.application.reporting.handlers.get_child_diagnostics import (
    handle_get_child_diagnostics,
)
from src.application.reporting.handlers.get_child_results import (
    ChildResults,
    handle_get_child_results,
)
from src.application.reporting.handlers.get_child_skill_results import (
    ChildSkillResults,
    handle_get_child_skill_results,
)
from src.application.reporting.queries.get_child_diagnostics import (
    GetChildDiagnosticsQuery,
)
from src.application.reporting.queries.get_child_results import GetChildResultsQuery
from src.application.reporting.queries.get_child_skill_results import (
    GetChildSkillResultsQuery,
)


class AssessmentResultsFacade:
    """Фасад application-слоя для read-only reporting контекста."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def get_child_diagnostics(self, *, child_id: UUID) -> dict[str, int]:
        return handle_get_child_diagnostics(
            GetChildDiagnosticsQuery(child_id=child_id),
            uow=self._uow,
        )

    def get_child_results(self, *, child_id: UUID) -> ChildResults:
        return handle_get_child_results(
            GetChildResultsQuery(child_id=child_id),
            uow=self._uow,
        )

    def get_child_skill_results(self, *, child_id: UUID) -> ChildSkillResults:
        return handle_get_child_skill_results(
            GetChildSkillResultsQuery(child_id=child_id),
            uow=self._uow,
        )
