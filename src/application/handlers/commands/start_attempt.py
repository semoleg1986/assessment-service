from uuid import uuid4

from src.application.commands.start_attempt import StartAttemptCommand
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.aggregates.attempt import AttemptAggregate
from src.domain.errors import InvariantViolationError, NotFoundError
from src.domain.value_objects.statuses import AssignmentStatus, AttemptStatus


def handle_start_attempt(
    command: StartAttemptCommand, uow: UnitOfWork
) -> AttemptAggregate:
    """
    Открыть новую попытку по назначению.

    :param command: Команда старта попытки.
    :type command: StartAttemptCommand
    :param uow: Unit of Work.
    :type uow: UnitOfWork
    :return: Созданная попытка.
    :rtype: AttemptAggregate
    """
    assignment = uow.assignments.get(command.assignment_id)
    if assignment is None:
        raise NotFoundError("assignment not found")
    if assignment.child_id != command.child_id:
        raise InvariantViolationError("assignment does not belong to child")

    assignments_by_child = {
        item.assignment_id: item
        for item in uow.assignments.list_by_child(command.child_id)
    }
    attempts_by_child = uow.attempts.list_by_child(command.child_id)

    # Idempotent resume: if there is an active attempt for the same assignment,
    # return it instead of creating a duplicate.
    for attempt in attempts_by_child:
        if (
            attempt.assignment_id == command.assignment_id
            and attempt.status == AttemptStatus.STARTED
        ):
            if assignment.status != AssignmentStatus.STARTED:
                assignment.mark_started()
                uow.assignments.save(assignment)
                uow.commit()
            return attempt

    # One test => one attempt per child. If attempt already exists for this test,
    # do not open a new one.
    for attempt in attempts_by_child:
        existing_assignment = assignments_by_child.get(attempt.assignment_id)
        if existing_assignment is None:
            continue
        if existing_assignment.test_id != assignment.test_id:
            continue
        if attempt.status == AttemptStatus.STARTED:
            return attempt
        raise InvariantViolationError("attempt for this test already exists")

    attempt = AttemptAggregate(
        attempt_id=uuid4(),
        assignment_id=command.assignment_id,
        child_id=command.child_id,
    )
    assignment.mark_started()
    uow.attempts.save(attempt)
    uow.assignments.save(assignment)
    uow.commit()
    return attempt
