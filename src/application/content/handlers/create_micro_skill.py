from src.application.content.commands.create_micro_skill import CreateMicroSkillCommand
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.content.micro_skill import ensure_predecessors_are_valid
from src.domain.content.micro_skill.entity import MicroSkillNode
from src.domain.errors import InvariantViolationError, NotFoundError


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
