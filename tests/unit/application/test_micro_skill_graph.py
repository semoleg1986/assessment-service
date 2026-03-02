import pytest

from src.application.commands.create_micro_skill import CreateMicroSkillCommand
from src.application.commands.create_subject import CreateSubjectCommand
from src.application.commands.link_micro_skill_predecessors import (
    LinkMicroSkillPredecessorsCommand,
)
from src.application.handlers.commands.create_micro_skill import (
    handle_create_micro_skill,
)
from src.application.handlers.commands.create_subject import handle_create_subject
from src.application.handlers.commands.link_micro_skill_predecessors import (
    handle_link_micro_skill_predecessors,
)
from src.application.handlers.queries.list_micro_skills import handle_list_micro_skills
from src.application.queries.list_micro_skills import ListMicroSkillsQuery
from src.domain.errors import InvariantViolationError
from src.domain.value_objects.statuses import CriticalityLevel
from src.infrastructure.uow import InMemoryUnitOfWork


def test_cycle_detection_when_linking_predecessors() -> None:
    uow = InMemoryUnitOfWork()
    handle_create_subject(CreateSubjectCommand(code="math", name="Math"), uow=uow)

    handle_create_micro_skill(
        CreateMicroSkillCommand(
            node_id="N1",
            subject_code="math",
            grade=2,
            section_code="R1",
            section_name="Section",
            micro_skill_name="Node1",
            predecessor_ids=[],
            criticality=CriticalityLevel.HIGH,
        ),
        uow=uow,
    )
    handle_create_micro_skill(
        CreateMicroSkillCommand(
            node_id="N2",
            subject_code="math",
            grade=2,
            section_code="R1",
            section_name="Section",
            micro_skill_name="Node2",
            predecessor_ids=["N1"],
            criticality=CriticalityLevel.MEDIUM,
        ),
        uow=uow,
    )

    with pytest.raises(InvariantViolationError):
        handle_link_micro_skill_predecessors(
            LinkMicroSkillPredecessorsCommand(node_id="N1", predecessor_ids=["N2"]),
            uow=uow,
        )


def test_blocks_count_is_calculated_from_reverse_dependencies() -> None:
    uow = InMemoryUnitOfWork()
    handle_create_subject(CreateSubjectCommand(code="math", name="Math"), uow=uow)

    handle_create_micro_skill(
        CreateMicroSkillCommand(
            node_id="N1",
            subject_code="math",
            grade=2,
            section_code="R1",
            section_name="Section",
            micro_skill_name="Node1",
            predecessor_ids=[],
            criticality=CriticalityLevel.HIGH,
        ),
        uow=uow,
    )
    handle_create_micro_skill(
        CreateMicroSkillCommand(
            node_id="N2",
            subject_code="math",
            grade=2,
            section_code="R1",
            section_name="Section",
            micro_skill_name="Node2",
            predecessor_ids=["N1"],
            criticality=CriticalityLevel.MEDIUM,
        ),
        uow=uow,
    )
    handle_create_micro_skill(
        CreateMicroSkillCommand(
            node_id="N3",
            subject_code="math",
            grade=2,
            section_code="R1",
            section_name="Section",
            micro_skill_name="Node3",
            predecessor_ids=["N2"],
            criticality=CriticalityLevel.LOW,
        ),
        uow=uow,
    )

    result = handle_list_micro_skills(ListMicroSkillsQuery(), uow=uow)
    blocks_by_node = {item["node"].node_id: item["blocks_count"] for item in result}

    assert blocks_by_node["N1"] == 2
    assert blocks_by_node["N2"] == 1
    assert blocks_by_node["N3"] == 0
