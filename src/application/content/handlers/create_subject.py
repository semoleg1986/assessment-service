from src.application.content.commands.create_subject import CreateSubjectCommand
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.content.subject.entity import Subject
from src.domain.errors import InvariantViolationError


def handle_create_subject(command: CreateSubjectCommand, uow: UnitOfWork) -> Subject:
    """
    Создать новый предмет.

    :param command: Команда создания предмета.
    :type command: CreateSubjectCommand
    :param uow: Unit of Work.
    :type uow: UnitOfWork
    :return: Созданный предмет.
    :rtype: Subject
    """
    if uow.subjects.get(command.code) is not None:
        raise InvariantViolationError("subject already exists")
    subject = Subject(code=command.code, name=command.name)
    uow.subjects.save(subject)
    uow.commit()
    return subject
