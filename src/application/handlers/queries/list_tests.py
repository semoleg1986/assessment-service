from src.application.ports.unit_of_work import UnitOfWork
from src.application.queries.list_tests import ListTestsQuery
from src.domain.aggregates.test_aggregate import AssessmentTest


def handle_list_tests(query: ListTestsQuery, uow: UnitOfWork) -> list[AssessmentTest]:
    """
    Получить список тестов.

    :param query: Запрос списка тестов.
    :type query: ListTestsQuery
    :param uow: Unit of Work.
    :type uow: UnitOfWork
    :return: Список тестов.
    :rtype: list[AssessmentTest]
    """
    _ = query
    return uow.tests.list()
