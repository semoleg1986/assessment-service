from __future__ import annotations

from collections import deque
from datetime import UTC, datetime

from src.application.commands.update_micro_skill import UpdateMicroSkillCommand
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.micro_skill_node import MicroSkillNode
from src.domain.errors import InvariantViolationError, NotFoundError


def _has_path(uow: UnitOfWork, src: str, target: str) -> bool:
    """Проверить достижимость target из src по predecessor-ребрам."""
    if src == target:
        return True

    visited: set[str] = set()
    queue = deque([src])
    while queue:
        node_id = queue.popleft()
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
                queue.append(pred)
    return False


def handle_update_micro_skill(
    command: UpdateMicroSkillCommand,
    uow: UnitOfWork,
) -> MicroSkillNode:
    """Обновить узел микро-умения с проверкой целостности графа."""
    node = uow.micro_skills.get(command.node_id)
    if node is None:
        raise NotFoundError("micro skill not found")

    topic = uow.topics.get(command.topic_code)
    if topic is None:
        raise NotFoundError("topic not found")
    if topic.subject_code != command.subject_code or topic.grade != command.grade:
        raise InvariantViolationError("topic does not match subject/grade")

    for pred in command.predecessor_ids:
        if pred == command.node_id:
            raise InvariantViolationError("self dependency is not allowed")
        if uow.micro_skills.get(pred) is None:
            raise NotFoundError(f"predecessor not found: {pred}")
        if _has_path(uow, pred, command.node_id):
            raise InvariantViolationError("cycle detected in micro-skill graph")

    if (
        node.subject_code == command.subject_code
        and node.topic_code == command.topic_code
        and node.grade == command.grade
        and node.section_code == command.section_code
        and node.section_name == command.section_name
        and node.micro_skill_name == command.micro_skill_name
        and node.predecessor_ids == command.predecessor_ids
        and node.criticality == command.criticality
        and node.source_ref == command.source_ref
        and node.description == command.description
        and node.status == command.status
        and node.external_ref == command.external_ref
    ):
        return node

    node.subject_code = command.subject_code
    node.topic_code = command.topic_code
    node.grade = command.grade
    node.section_code = command.section_code
    node.section_name = command.section_name
    node.micro_skill_name = command.micro_skill_name
    node.predecessor_ids = command.predecessor_ids
    node.criticality = command.criticality
    node.source_ref = command.source_ref
    node.description = command.description
    node.status = command.status
    node.external_ref = command.external_ref
    node.version += 1
    node.updated_at = datetime.now(UTC)

    uow.micro_skills.save(node)
    uow.commit()
    return node
