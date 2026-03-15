import pytest

from src.application.content.commands.create_micro_skill import CreateMicroSkillCommand
from src.application.content.commands.create_subject import CreateSubjectCommand
from src.application.content.commands.create_test import (
    CreateTestCommand,
    QuestionInput,
)
from src.application.content.commands.create_topic import CreateTopicCommand
from src.application.content.commands.delete_micro_skill import DeleteMicroSkillCommand
from src.application.content.commands.link_micro_skill_predecessors import (
    LinkMicroSkillPredecessorsCommand,
)
from src.application.content.commands.update_micro_skill import UpdateMicroSkillCommand
from src.application.content.handlers.create_micro_skill import (
    handle_create_micro_skill,
)
from src.application.content.handlers.create_subject import handle_create_subject
from src.application.content.handlers.create_test import handle_create_test
from src.application.content.handlers.create_topic import handle_create_topic
from src.application.content.handlers.delete_micro_skill import (
    handle_delete_micro_skill,
)
from src.application.content.handlers.link_micro_skill_predecessors import (
    handle_link_micro_skill_predecessors,
)
from src.application.content.handlers.list_micro_skills import handle_list_micro_skills
from src.application.content.handlers.update_micro_skill import (
    handle_update_micro_skill,
)
from src.application.content.queries.list_micro_skills import ListMicroSkillsQuery
from src.domain.errors import InvariantViolationError, NotFoundError
from src.domain.shared.statuses import CriticalityLevel
from src.infrastructure.uow import InMemoryUnitOfWork


def _seed_math_topic(uow: InMemoryUnitOfWork) -> None:
    handle_create_subject(CreateSubjectCommand(code="math", name="Math"), uow=uow)
    handle_create_topic(
        CreateTopicCommand(code="M2-T1", subject_code="math", grade=2, name="Topic 1"),
        uow=uow,
    )


def test_cycle_detection_when_linking_predecessors() -> None:
    uow = InMemoryUnitOfWork()
    _seed_math_topic(uow)

    handle_create_micro_skill(
        CreateMicroSkillCommand(
            node_id="N1",
            subject_code="math",
            topic_code="M2-T1",
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
            topic_code="M2-T1",
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
    _seed_math_topic(uow)

    handle_create_micro_skill(
        CreateMicroSkillCommand(
            node_id="N1",
            subject_code="math",
            topic_code="M2-T1",
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
            topic_code="M2-T1",
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
            topic_code="M2-T1",
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


def test_link_updates_micro_skill_version_and_timestamp() -> None:
    uow = InMemoryUnitOfWork()
    _seed_math_topic(uow)

    handle_create_micro_skill(
        CreateMicroSkillCommand(
            node_id="N1",
            subject_code="math",
            topic_code="M2-T1",
            grade=2,
            section_code="R1",
            section_name="Section",
            micro_skill_name="Node1",
            predecessor_ids=[],
            criticality=CriticalityLevel.HIGH,
        ),
        uow=uow,
    )
    node2 = handle_create_micro_skill(
        CreateMicroSkillCommand(
            node_id="N2",
            subject_code="math",
            topic_code="M2-T1",
            grade=2,
            section_code="R1",
            section_name="Section",
            micro_skill_name="Node2",
            predecessor_ids=[],
            criticality=CriticalityLevel.MEDIUM,
        ),
        uow=uow,
    )

    initial_updated_at = node2.updated_at
    linked = handle_link_micro_skill_predecessors(
        LinkMicroSkillPredecessorsCommand(node_id="N2", predecessor_ids=["N1"]),
        uow=uow,
    )
    assert linked.version == 2
    assert linked.updated_at > initial_updated_at

    same_link = handle_link_micro_skill_predecessors(
        LinkMicroSkillPredecessorsCommand(node_id="N2", predecessor_ids=["N1"]),
        uow=uow,
    )
    assert same_link.version == 2
    assert same_link.updated_at == linked.updated_at


def test_create_micro_skill_fails_for_unknown_topic() -> None:
    uow = InMemoryUnitOfWork()
    handle_create_subject(CreateSubjectCommand(code="math", name="Math"), uow=uow)

    with pytest.raises(NotFoundError):
        handle_create_micro_skill(
            CreateMicroSkillCommand(
                node_id="N1",
                subject_code="math",
                topic_code="M2-TX",
                grade=2,
                section_code="R1",
                section_name="Section",
                micro_skill_name="Node1",
                predecessor_ids=[],
                criticality=CriticalityLevel.HIGH,
            ),
            uow=uow,
        )


def test_create_micro_skill_fails_when_topic_mismatch() -> None:
    uow = InMemoryUnitOfWork()
    handle_create_subject(CreateSubjectCommand(code="math", name="Math"), uow=uow)
    handle_create_topic(
        CreateTopicCommand(code="M3-T1", subject_code="math", grade=3, name="Topic 3"),
        uow=uow,
    )

    with pytest.raises(InvariantViolationError):
        handle_create_micro_skill(
            CreateMicroSkillCommand(
                node_id="N1",
                subject_code="math",
                topic_code="M3-T1",
                grade=2,
                section_code="R1",
                section_name="Section",
                micro_skill_name="Node1",
                predecessor_ids=[],
                criticality=CriticalityLevel.HIGH,
            ),
            uow=uow,
        )


def test_update_micro_skill_updates_version_metadata_and_links() -> None:
    uow = InMemoryUnitOfWork()
    _seed_math_topic(uow)
    handle_create_micro_skill(
        CreateMicroSkillCommand(
            node_id="N1",
            subject_code="math",
            topic_code="M2-T1",
            grade=2,
            section_code="R1",
            section_name="Section",
            micro_skill_name="Node1",
            predecessor_ids=[],
            criticality=CriticalityLevel.HIGH,
        ),
        uow=uow,
    )
    created = handle_create_micro_skill(
        CreateMicroSkillCommand(
            node_id="N2",
            subject_code="math",
            topic_code="M2-T1",
            grade=2,
            section_code="R1",
            section_name="Section",
            micro_skill_name="Node2",
            predecessor_ids=[],
            criticality=CriticalityLevel.MEDIUM,
            description="Initial",
        ),
        uow=uow,
    )

    updated = handle_update_micro_skill(
        UpdateMicroSkillCommand(
            node_id="N2",
            subject_code="math",
            topic_code="M2-T1",
            grade=2,
            section_code="R2",
            section_name="Section 2",
            micro_skill_name="Node2 updated",
            predecessor_ids=["N1"],
            criticality=CriticalityLevel.LOW,
            description="Updated",
            status=created.status,
            source_ref="manual",
            external_ref="ref-2",
        ),
        uow=uow,
    )

    assert updated.version == 2
    assert updated.section_code == "R2"
    assert updated.micro_skill_name == "Node2 updated"
    assert updated.predecessor_ids == ["N1"]
    assert updated.description == "Updated"
    assert updated.source_ref == "manual"
    assert updated.external_ref == "ref-2"


def test_delete_micro_skill_fails_when_referenced_as_predecessor() -> None:
    uow = InMemoryUnitOfWork()
    _seed_math_topic(uow)
    handle_create_micro_skill(
        CreateMicroSkillCommand(
            node_id="N1",
            subject_code="math",
            topic_code="M2-T1",
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
            topic_code="M2-T1",
            grade=2,
            section_code="R1",
            section_name="Section",
            micro_skill_name="Node2",
            predecessor_ids=["N1"],
            criticality=CriticalityLevel.MEDIUM,
        ),
        uow=uow,
    )

    with pytest.raises(InvariantViolationError, match="referenced as predecessor"):
        handle_delete_micro_skill(DeleteMicroSkillCommand(node_id="N1"), uow=uow)


def test_delete_micro_skill_fails_when_referenced_by_test_question() -> None:
    uow = InMemoryUnitOfWork()
    _seed_math_topic(uow)
    handle_create_micro_skill(
        CreateMicroSkillCommand(
            node_id="N1",
            subject_code="math",
            topic_code="M2-T1",
            grade=2,
            section_code="R1",
            section_name="Section",
            micro_skill_name="Node1",
            predecessor_ids=[],
            criticality=CriticalityLevel.HIGH,
        ),
        uow=uow,
    )
    handle_create_test(
        CreateTestCommand(
            subject_code="math",
            grade=2,
            questions=[
                QuestionInput(
                    node_id="N1",
                    text="1+1?",
                    answer_key="2",
                    max_score=1,
                )
            ],
        ),
        uow=uow,
    )

    with pytest.raises(InvariantViolationError, match="referenced by test"):
        handle_delete_micro_skill(DeleteMicroSkillCommand(node_id="N1"), uow=uow)


def test_delete_micro_skill_removes_unreferenced_node() -> None:
    uow = InMemoryUnitOfWork()
    _seed_math_topic(uow)
    handle_create_micro_skill(
        CreateMicroSkillCommand(
            node_id="N1",
            subject_code="math",
            topic_code="M2-T1",
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
            topic_code="M2-T1",
            grade=2,
            section_code="R1",
            section_name="Section",
            micro_skill_name="Node2",
            predecessor_ids=[],
            criticality=CriticalityLevel.MEDIUM,
        ),
        uow=uow,
    )

    handle_delete_micro_skill(DeleteMicroSkillCommand(node_id="N2"), uow=uow)

    assert uow.micro_skills.get("N2") is None
