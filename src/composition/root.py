from __future__ import annotations

from src.application.ports.fixture_cleanup import (
    FixtureCleanupCounts,
    FixtureCleanupExecution,
    FixtureCleanupFilters,
    FixtureCleanupService,
    FixtureCleanupUnsupportedError,
)
from src.application.ports.unit_of_work import UnitOfWork
from src.infrastructure.maintenance import (
    FixtureCleanupUnsupportedError as InfraFixtureCleanupUnsupportedError,
)
from src.infrastructure.maintenance import run_fixture_cleanup
from src.infrastructure.maintenance.fixture_cleanup import (
    FixtureCleanupExecution as InfraFixtureCleanupExecution,
)
from src.infrastructure.maintenance.fixture_cleanup import (
    FixtureCleanupFilters as InfraFixtureCleanupFilters,
)
from src.infrastructure.uow import build_uow


class InfraFixtureCleanupService(FixtureCleanupService):
    def run(
        self,
        *,
        uow: UnitOfWork,
        dry_run: bool,
        filters: FixtureCleanupFilters,
    ) -> FixtureCleanupExecution:
        infra_filters = InfraFixtureCleanupFilters(
            subject_code_patterns=filters.subject_code_patterns,
            topic_code_patterns=filters.topic_code_patterns,
            node_id_patterns=filters.node_id_patterns,
        )
        try:
            result = run_fixture_cleanup(
                uow=uow,
                dry_run=dry_run,
                filters=infra_filters,
            )
        except InfraFixtureCleanupUnsupportedError as exc:
            raise FixtureCleanupUnsupportedError(str(exc)) from exc
        return _map_cleanup_execution(result)


def _map_cleanup_execution(
    result: InfraFixtureCleanupExecution,
) -> FixtureCleanupExecution:
    return FixtureCleanupExecution(
        dry_run=result.dry_run,
        filters=FixtureCleanupFilters(
            subject_code_patterns=result.filters.subject_code_patterns,
            topic_code_patterns=result.filters.topic_code_patterns,
            node_id_patterns=result.filters.node_id_patterns,
        ),
        matched=FixtureCleanupCounts(
            subjects=result.matched.subjects,
            topics=result.matched.topics,
            micro_skills=result.matched.micro_skills,
            tests=result.matched.tests,
            questions=result.matched.questions,
            assignments=result.matched.assignments,
            attempts=result.matched.attempts,
            answers=result.matched.answers,
        ),
        deleted=FixtureCleanupCounts(
            subjects=result.deleted.subjects,
            topics=result.deleted.topics,
            micro_skills=result.deleted.micro_skills,
            tests=result.deleted.tests,
            questions=result.deleted.questions,
            assignments=result.deleted.assignments,
            attempts=result.deleted.attempts,
            answers=result.deleted.answers,
        ),
    )


_uow = build_uow()
_fixture_cleanup_service = InfraFixtureCleanupService()


def get_uow() -> UnitOfWork:
    return _uow


def get_fixture_cleanup_service() -> FixtureCleanupService:
    return _fixture_cleanup_service
