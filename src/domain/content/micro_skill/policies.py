from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from uuid import UUID

from src.domain.errors import InvariantViolationError, NotFoundError


def _has_path(
    *,
    src: str,
    target: str,
    get_predecessors: Callable[[str], list[str] | None],
) -> bool:
    if src == target:
        return True

    visited: set[str] = set()
    queue = deque([src])
    while queue:
        node_id = queue.popleft()
        if node_id in visited:
            continue
        visited.add(node_id)

        predecessors = get_predecessors(node_id)
        if predecessors is None:
            continue

        for pred in predecessors:
            if pred == target:
                return True
            if pred not in visited:
                queue.append(pred)
    return False


def ensure_predecessors_are_valid(
    *,
    node_id: str,
    predecessor_ids: list[str],
    exists: Callable[[str], bool],
    get_predecessors: Callable[[str], list[str] | None],
) -> None:
    """Проверить predecessor-ссылки и отсутствие циклов в графе."""
    for pred in predecessor_ids:
        if pred == node_id:
            raise InvariantViolationError("self dependency is not allowed")
        if not exists(pred):
            raise NotFoundError(f"predecessor not found: {pred}")
        if _has_path(src=pred, target=node_id, get_predecessors=get_predecessors):
            raise InvariantViolationError("cycle detected in micro-skill graph")


def ensure_micro_skill_can_be_deleted(
    *,
    node_id: str,
    dependent_node_ids: Iterable[str],
    test_ids_with_reference: Iterable[UUID],
) -> None:
    """Проверить, что узел можно удалить без нарушения ссылочной целостности."""
    dependent_id = next(iter(dependent_node_ids), None)
    if dependent_id is not None:
        raise InvariantViolationError(
            f"micro skill is referenced as predecessor by: {dependent_id}"
        )

    test_id = next(iter(test_ids_with_reference), None)
    if test_id is not None:
        raise InvariantViolationError(f"micro skill is referenced by test: {test_id}")
