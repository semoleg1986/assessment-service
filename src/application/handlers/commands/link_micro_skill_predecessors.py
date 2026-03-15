from src.application.commands.link_micro_skill_predecessors import (
    LinkMicroSkillPredecessorsCommand,
)
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.micro_skill_node import MicroSkillNode
from src.domain.errors import NotFoundError
from src.domain.services import ensure_predecessors_are_valid


def handle_link_micro_skill_predecessors(
    command: LinkMicroSkillPredecessorsCommand,
    uow: UnitOfWork,
) -> MicroSkillNode:
    """
    Обновить список предшественников у узла микро-умения.

    :param command: Команда связывания узла с predecessor-узлами.
    :type command: LinkMicroSkillPredecessorsCommand
    :param uow: Unit of Work.
    :type uow: UnitOfWork
    :return: Обновлённый узел.
    :rtype: MicroSkillNode
    """
    node = uow.micro_skills.get(command.node_id)
    if node is None:
        raise NotFoundError("micro skill not found")

    ensure_predecessors_are_valid(
        node_id=command.node_id,
        predecessor_ids=command.predecessor_ids,
        exists=lambda pred: uow.micro_skills.get(pred) is not None,
        get_predecessors=(
            lambda node_id: (
                current.predecessor_ids
                if (current := uow.micro_skills.get(node_id)) is not None
                else None
            )
        ),
    )

    changed = node.relink_predecessors(command.predecessor_ids)
    if not changed:
        return node

    uow.micro_skills.save(node)
    uow.commit()
    return node
