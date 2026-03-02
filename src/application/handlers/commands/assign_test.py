from uuid import uuid4

from src.application.commands.assign_test import AssignTestCommand
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.aggregates.assignment import AssignmentAggregate
from src.domain.errors import NotFoundError


def handle_assign_test(
    command: AssignTestCommand, uow: UnitOfWork
) -> AssignmentAggregate:
    """
    Назначить тест ребёнку.

    :param command: Команда назначения теста.
    :type command: AssignTestCommand
    :param uow: Unit of Work.
    :type uow: UnitOfWork
    :return: Созданное назначение.
    :rtype: AssignmentAggregate
    """
    test = uow.tests.get(command.test_id)
    if test is None:
        raise NotFoundError("test not found")
    assignment = AssignmentAggregate(
        assignment_id=uuid4(),
        test_id=command.test_id,
        child_id=command.child_id,
    )
    uow.assignments.save(assignment)
    uow.commit()
    return assignment
