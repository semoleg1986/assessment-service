from src.application.commands.create_micro_skill import CreateMicroSkillCommand
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.micro_skill_node import MicroSkillNode
from src.domain.errors import InvariantViolationError, NotFoundError


def _has_path(uow: UnitOfWork, src: str, target: str) -> bool:
    """
    Проверить достижимость `target` из `src` по predecessor-ребрам.

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


def handle_create_micro_skill(
    command: CreateMicroSkillCommand,
    uow: UnitOfWork,
) -> MicroSkillNode:
    """
    Создать узел микро-умения с проверкой инвариантов графа.

    :param command: Команда создания узла.
    :type command: CreateMicroSkillCommand
    :param uow: Unit of Work.
    :type uow: UnitOfWork
    :return: Созданный узел.
    :rtype: MicroSkillNode
    """
    if uow.subjects.get(command.subject_code) is None:
        raise NotFoundError("subject not found")
    topic = uow.topics.get(command.topic_code)
    if topic is None:
        raise NotFoundError("topic not found")
    if topic.subject_code != command.subject_code or topic.grade != command.grade:
        raise InvariantViolationError("topic does not match subject/grade")
    if uow.micro_skills.get(command.node_id) is not None:
        raise InvariantViolationError("micro skill already exists")

    for pred in command.predecessor_ids:
        if uow.micro_skills.get(pred) is None:
            raise NotFoundError(f"predecessor not found: {pred}")
        if _has_path(uow, pred, command.node_id):
            raise InvariantViolationError("cycle detected in micro-skill graph")

    node = MicroSkillNode(
        node_id=command.node_id,
        subject_code=command.subject_code,
        grade=command.grade,
        topic_code=command.topic_code,
        section_code=command.section_code,
        section_name=command.section_name,
        micro_skill_name=command.micro_skill_name,
        predecessor_ids=command.predecessor_ids,
        criticality=command.criticality,
        source_ref=command.source_ref,
        description=command.description,
        status=command.status,
        external_ref=command.external_ref,
        version=1,
    )
    uow.micro_skills.save(node)
    uow.commit()
    return node
