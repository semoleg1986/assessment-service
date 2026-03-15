from __future__ import annotations

from src.application.content.commands.delete_micro_skill import DeleteMicroSkillCommand
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.errors import NotFoundError
from src.domain.services import ensure_micro_skill_can_be_deleted


def handle_delete_micro_skill(
    command: DeleteMicroSkillCommand,
    uow: UnitOfWork,
) -> None:
    """Удалить узел микро-умения, если на него нет активных ссылок."""
    node = uow.micro_skills.get(command.node_id)
    if node is None:
        raise NotFoundError("micro skill not found")

    all_nodes = uow.micro_skills.list()
    dependent_node_ids = (
        dependent.node_id
        for dependent in all_nodes
        if dependent.node_id != command.node_id
        and command.node_id in dependent.predecessor_ids
    )
    test_ids_with_reference = (
        test.test_id
        for test in uow.tests.list()
        if any(question.node_id == command.node_id for question in test.questions)
    )
    ensure_micro_skill_can_be_deleted(
        node_id=command.node_id,
        dependent_node_ids=dependent_node_ids,
        test_ids_with_reference=test_ids_with_reference,
    )

    uow.micro_skills.delete(command.node_id)
    uow.commit()
