from __future__ import annotations

from typing import Any

from src.application.facade.assessment_content_facade import AssessmentContentFacade
from src.application.facade.assessment_import_facade import AssessmentImportFacade
from src.application.facade.assessment_results_facade import AssessmentResultsFacade
from src.application.ports.fixture_cleanup import FixtureCleanupService
from src.application.ports.unit_of_work import UnitOfWork


class AssessmentAdminFacade:
    """
    Устаревший совместимый фасад.

    Новая структура: AssessmentContentFacade + AssessmentImportFacade +
    AssessmentResultsFacade. Этот класс сохранен, чтобы не ломать внешний код
    и интеграционные тесты, которые все еще импортируют AssessmentAdminFacade.
    """

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        fixture_cleanup_service: FixtureCleanupService,
    ) -> None:
        self.content = AssessmentContentFacade(
            uow=uow,
            fixture_cleanup_service=fixture_cleanup_service,
        )
        self.imports = AssessmentImportFacade(uow=uow)
        self.results = AssessmentResultsFacade(uow=uow)

    def __getattr__(self, name: str) -> Any:
        for delegate in (self.content, self.imports, self.results):
            if hasattr(delegate, name):
                return getattr(delegate, name)
        raise AttributeError(name)
