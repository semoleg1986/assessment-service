from src.application.ports.unit_of_work import UnitOfWork
from src.application.queries.get_test_by_id import GetTestByIdQuery
from src.domain.aggregates.test_aggregate import AssessmentTest


def handle_get_test_by_id(
    query: GetTestByIdQuery,
    *,
    uow: UnitOfWork,
) -> AssessmentTest | None:
    return uow.tests.get(query.test_id)
