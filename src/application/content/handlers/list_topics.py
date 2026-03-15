from src.application.content.queries.list_topics import ListTopicsQuery
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.content.topic.entity import Topic


def handle_list_topics(query: ListTopicsQuery, uow: UnitOfWork) -> list[Topic]:
    """
    Получить список тем.

    :param query: Запрос списка тем.
    :type query: ListTopicsQuery
    :param uow: Unit of Work.
    :type uow: UnitOfWork
    :return: Список тем.
    :rtype: list[Topic]
    """
    _ = query
    return uow.topics.list()
