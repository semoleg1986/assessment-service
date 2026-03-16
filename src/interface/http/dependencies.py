from src.application.ports.fixture_cleanup import FixtureCleanupService
from src.application.ports.unit_of_work import UnitOfWork
from src.composition.root import (
    get_fixture_cleanup_service as _get_fixture_cleanup_service,
)
from src.composition.root import get_uow as _get_uow


def get_uow() -> UnitOfWork:
    return _get_uow()


def get_fixture_cleanup_service() -> FixtureCleanupService:
    return _get_fixture_cleanup_service()
