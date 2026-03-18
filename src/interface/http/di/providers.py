from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from dishka import Provider, Scope, provide

from src.application.facade import AssessmentAdminFacade, AssessmentUserFacade
from src.application.ports.fixture_cleanup import FixtureCleanupService
from src.application.ports.unit_of_work import UnitOfWork
from src.interface.http import dependencies as deps


@dataclass(slots=True)
class _AppScopedUow:
    value: UnitOfWork


class AppProvider(Provider):  # type: ignore[misc]
    @provide(scope=Scope.APP)  # type: ignore[misc]
    def provide_app_uow(self) -> _AppScopedUow:
        return _AppScopedUow(value=deps.get_uow())

    @provide(scope=Scope.REQUEST)  # type: ignore[misc]
    def provide_uow(self, app_uow: _AppScopedUow) -> Iterator[UnitOfWork]:
        try:
            yield app_uow.value
        finally:
            close = getattr(app_uow.value, "close", None)
            if callable(close):
                close()

    @provide(scope=Scope.APP)  # type: ignore[misc]
    def provide_fixture_cleanup_service(self) -> FixtureCleanupService:
        return deps.get_fixture_cleanup_service()

    @provide(scope=Scope.REQUEST)  # type: ignore[misc]
    def provide_admin_facade(
        self,
        uow: UnitOfWork,
        fixture_cleanup_service: FixtureCleanupService,
    ) -> AssessmentAdminFacade:
        return AssessmentAdminFacade(
            uow=uow,
            fixture_cleanup_service=fixture_cleanup_service,
        )

    @provide(scope=Scope.REQUEST)  # type: ignore[misc]
    def provide_user_facade(self, uow: UnitOfWork) -> AssessmentUserFacade:
        return AssessmentUserFacade(uow=uow)
