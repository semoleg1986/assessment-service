from uuid import uuid4

from src.application.delivery.commands.assign_test import AssignTestCommand
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.delivery.assignment.aggregate import AssignmentAggregate
from src.domain.errors import InvariantViolationError, NotFoundError
from src.domain.shared.statuses import AttemptStatus


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

    assignments_by_child = uow.assignments.list_by_child(command.child_id)
    same_test_assignments = [
        assignment
        for assignment in assignments_by_child
        if assignment.test_id == command.test_id
    ]

    if not command.retake and same_test_assignments:
        raise InvariantViolationError(
            "assignment for this test already exists, use retake=true"
        )

    attempt_no = 1
    if command.retake:
        if not same_test_assignments:
            raise InvariantViolationError("retake requires existing assignment")

        assignments_by_id = {
            assignment.assignment_id: assignment for assignment in assignments_by_child
        }
        attempts_by_child = uow.attempts.list_by_child(command.child_id)
        attempts_for_same_test = [
            attempt
            for attempt in attempts_by_child
            if assignments_by_id.get(attempt.assignment_id) is not None
            and assignments_by_id[attempt.assignment_id].test_id == command.test_id
        ]
        if not attempts_for_same_test:
            raise InvariantViolationError(
                "retake requires at least one existing attempt for this test"
            )
        if any(
            attempt.status == AttemptStatus.STARTED
            for attempt in attempts_for_same_test
        ):
            raise InvariantViolationError(
                "cannot create retake while previous attempt is started"
            )
        attempt_no = (
            max(assignment.attempt_no for assignment in same_test_assignments) + 1
        )

    assignment = AssignmentAggregate(
        assignment_id=uuid4(),
        test_id=command.test_id,
        child_id=command.child_id,
        attempt_no=attempt_no,
    )
    uow.assignments.save(assignment)
    uow.commit()
    return assignment
