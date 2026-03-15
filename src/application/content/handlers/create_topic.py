from src.application.content.commands.create_topic import CreateTopicCommand
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.content.topic.entity import Topic
from src.domain.errors import InvariantViolationError, NotFoundError


def handle_create_topic(command: CreateTopicCommand, uow: UnitOfWork) -> Topic:
    """
    Создать тему в рамках предмета.

    :param command: Команда создания темы.
    :type command: CreateTopicCommand
    :param uow: Unit of Work.
    :type uow: UnitOfWork
    :return: Созданная тема.
    :rtype: Topic
    """
    if uow.subjects.get(command.subject_code) is None:
        raise NotFoundError("subject not found")
    if uow.topics.get(command.code) is not None:
        raise InvariantViolationError("topic already exists")
    topic = Topic(
        code=command.code,
        subject_code=command.subject_code,
        grade=command.grade,
        name=command.name,
    )
    uow.topics.save(topic)
    uow.commit()
    return topic
