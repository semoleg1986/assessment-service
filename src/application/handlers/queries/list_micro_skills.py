from collections import deque
from typing import TypedDict

from src.application.ports.unit_of_work import UnitOfWork
from src.application.queries.list_micro_skills import ListMicroSkillsQuery
from src.domain.entities.micro_skill_node import MicroSkillNode


class MicroSkillWithBlocks(TypedDict):
    node: MicroSkillNode
    blocks_count: int


def _collect_dependents_count(node_id: str, reverse_edges: dict[str, set[str]]) -> int:
    """
    Посчитать количество узлов, зависящих от указанного узла.

    :param node_id: Идентификатор узла.
    :type node_id: str
    :param reverse_edges: Обратный индекс зависимостей.
    :type reverse_edges: dict[str, set[str]]
    :return: Количество зависимых узлов.
    :rtype: int
    """
    visited: set[str] = set()
    queue = deque([node_id])
    while queue:
        current = queue.popleft()
        for dep in reverse_edges.get(current, set()):
            if dep in visited:
                continue
            visited.add(dep)
            queue.append(dep)
    return len(visited)


def handle_list_micro_skills(
    query: ListMicroSkillsQuery, uow: UnitOfWork
) -> list[MicroSkillWithBlocks]:
    """
    Вернуть список узлов микро-умений с вычисленным `blocks_count`.

    :param query: Запрос списка узлов.
    :type query: ListMicroSkillsQuery
    :param uow: Unit of Work.
    :type uow: UnitOfWork
    :return: Список узлов с метрикой блокировки.
    :rtype: list[MicroSkillWithBlocks]
    """
    _ = query
    nodes = uow.micro_skills.list()
    reverse_edges: dict[str, set[str]] = {}
    for n in nodes:
        reverse_edges.setdefault(n.node_id, set())
        for pred in n.predecessor_ids:
            reverse_edges.setdefault(pred, set()).add(n.node_id)

    return [
        {
            "node": n,
            "blocks_count": _collect_dependents_count(n.node_id, reverse_edges),
        }
        for n in nodes
    ]
