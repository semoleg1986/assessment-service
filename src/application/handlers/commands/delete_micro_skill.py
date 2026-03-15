from __future__ import annotations

from src.application.commands.delete_micro_skill import DeleteMicroSkillCommand
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.errors import InvariantViolationError, NotFoundError


def handle_delete_micro_skill(
    command: DeleteMicroSkillCommand,
    uow: UnitOfWork,
) -> None:
    """Удалить узел микро-умения, если на него нет активных ссылок."""
    node = uow.micro_skills.get(command.node_id)
    if node is None:
        raise NotFoundError("micro skill not found")

    for dependent in uow.micro_skills.list():
        if dependent.node_id == command.node_id:
            continue
        if command.node_id in dependent.predecessor_ids:
            raise InvariantViolationError(
                f"micro skill is referenced as predecessor by: {dependent.node_id}"
            )

    for test in uow.tests.list():
        for question in test.questions:
            if question.node_id == command.node_id:
                raise InvariantViolationError(
                    f"micro skill is referenced by test: {test.test_id}"
                )

    uow.micro_skills.delete(command.node_id)
    uow.commit()
