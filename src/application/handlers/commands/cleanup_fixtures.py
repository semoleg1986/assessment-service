from src.application.commands.cleanup_fixtures import CleanupFixturesCommand
from src.application.ports.fixture_cleanup import (
    FixtureCleanupExecution,
    FixtureCleanupFilters,
    FixtureCleanupService,
)
from src.application.ports.unit_of_work import UnitOfWork


def handle_cleanup_fixtures(
    command: CleanupFixturesCommand,
    *,
    uow: UnitOfWork,
    service: FixtureCleanupService,
) -> FixtureCleanupExecution:
    return service.run(
        uow=uow,
        dry_run=command.dry_run,
        filters=FixtureCleanupFilters(
            subject_code_patterns=command.subject_code_patterns,
            topic_code_patterns=command.topic_code_patterns,
            node_id_patterns=command.node_id_patterns,
        ),
    )
