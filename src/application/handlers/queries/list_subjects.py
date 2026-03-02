from src.application.ports.unit_of_work import UnitOfWork
from src.application.queries.list_subjects import ListSubjectsQuery
from src.domain.entities.subject import Subject


def handle_list_subjects(query: ListSubjectsQuery, uow: UnitOfWork) -> list[Subject]:
    """
    Получить список предметов.

    :param query: Запрос списка предметов.
    :type query: ListSubjectsQuery
    :param uow: Unit of Work.
    :type uow: UnitOfWork
    :return: Список предметов.
    :rtype: list[Subject]
    """
    _ = query
    return uow.subjects.list()
