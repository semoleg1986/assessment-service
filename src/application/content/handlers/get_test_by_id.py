from src.application.content.queries.get_test_by_id import GetTestByIdQuery
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.content.test.entity import AssessmentTest


def handle_get_test_by_id(
    query: GetTestByIdQuery,
    *,
    uow: UnitOfWork,
) -> AssessmentTest | None:
    return uow.tests.get(query.test_id)
