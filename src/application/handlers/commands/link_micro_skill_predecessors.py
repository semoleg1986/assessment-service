from src.application.commands.link_micro_skill_predecessors import (
    LinkMicroSkillPredecessorsCommand,
)
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.micro_skill_node import MicroSkillNode
from src.domain.errors import InvariantViolationError, NotFoundError


def _has_path(uow: UnitOfWork, src: str, target: str) -> bool:
    """
    Проверить достижимость `target` из `src` для детекции циклов.

    :param uow: Unit of Work.
    :type uow: UnitOfWork
    :param src: Исходный узел.
    :type src: str
    :param target: Целевой узел.
    :type target: str
    :return: True, если путь существует.
    :rtype: bool
    """
    if src == target:
        return True
    visited: set[str] = set()
    stack = [src]
    while stack:
        node_id = stack.pop()
        if node_id in visited:
            continue
        visited.add(node_id)
        node = uow.micro_skills.get(node_id)
        if node is None:
            continue
        for pred in node.predecessor_ids:
            if pred == target:
                return True
            if pred not in visited:
                stack.append(pred)
    return False


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

    for pred in command.predecessor_ids:
        if pred == command.node_id:
            raise InvariantViolationError("self dependency is not allowed")
        if uow.micro_skills.get(pred) is None:
            raise NotFoundError(f"predecessor not found: {pred}")
        if _has_path(uow, pred, command.node_id):
            raise InvariantViolationError("cycle detected in micro-skill graph")

    node.predecessor_ids = command.predecessor_ids
    uow.micro_skills.save(node)
    uow.commit()
    return node
