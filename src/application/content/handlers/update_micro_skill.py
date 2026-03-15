from __future__ import annotations

from src.application.content.commands.update_micro_skill import UpdateMicroSkillCommand
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.content.micro_skill.entity import MicroSkillNode
from src.domain.errors import InvariantViolationError, NotFoundError
from src.domain.services import ensure_predecessors_are_valid


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

    changed = node.update_details(
        subject_code=command.subject_code,
        topic_code=command.topic_code,
        grade=command.grade,
        section_code=command.section_code,
        section_name=command.section_name,
        micro_skill_name=command.micro_skill_name,
        predecessor_ids=command.predecessor_ids,
        criticality=command.criticality,
        source_ref=command.source_ref,
        description=command.description,
        status=command.status,
        external_ref=command.external_ref,
    )
    if not changed:
        return node

    uow.micro_skills.save(node)
    uow.commit()
    return node
