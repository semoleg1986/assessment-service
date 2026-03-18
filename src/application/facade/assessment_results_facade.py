from __future__ import annotations

from src.application.facade.inputs import ChildScopedInput
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

    def get_child_diagnostics(self, *, payload: ChildScopedInput) -> dict[str, int]:
        return handle_get_child_diagnostics(
            GetChildDiagnosticsQuery(child_id=payload.child_id),
            uow=self._uow,
        )

    def get_child_results(self, *, payload: ChildScopedInput) -> ChildResults:
        return handle_get_child_results(
            GetChildResultsQuery(child_id=payload.child_id),
            uow=self._uow,
        )

    def get_child_skill_results(
        self, *, payload: ChildScopedInput
    ) -> ChildSkillResults:
        return handle_get_child_skill_results(
            GetChildSkillResultsQuery(child_id=payload.child_id),
            uow=self._uow,
        )
