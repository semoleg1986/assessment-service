from __future__ import annotations

from uuid import UUID

from src.application.content.commands.cleanup_fixtures import CleanupFixturesCommand
from src.application.content.commands.create_micro_skill import CreateMicroSkillCommand
from src.application.content.commands.create_subject import CreateSubjectCommand
from src.application.content.commands.create_test import (
    CreateTestCommand,
    QuestionInput,
)
from src.application.content.commands.create_topic import CreateTopicCommand
from src.application.content.commands.delete_micro_skill import DeleteMicroSkillCommand
from src.application.content.commands.import_content import (
    ImportContentCommand,
    ImportContentResult,
)
from src.application.content.commands.link_micro_skill_predecessors import (
    LinkMicroSkillPredecessorsCommand,
)
from src.application.content.commands.update_micro_skill import UpdateMicroSkillCommand
from src.application.content.handlers.cleanup_fixtures import handle_cleanup_fixtures
from src.application.content.handlers.create_micro_skill import (
    handle_create_micro_skill,
)
from src.application.content.handlers.create_subject import handle_create_subject
from src.application.content.handlers.create_test import handle_create_test
from src.application.content.handlers.create_topic import handle_create_topic
from src.application.content.handlers.delete_micro_skill import (
    handle_delete_micro_skill,
)
from src.application.content.handlers.get_test_by_id import handle_get_test_by_id
from src.application.content.handlers.import_content import handle_import_content
from src.application.content.handlers.link_micro_skill_predecessors import (
    handle_link_micro_skill_predecessors,
)
from src.application.content.handlers.list_micro_skills import (
    MicroSkillWithBlocks,
    handle_list_micro_skills,
)
from src.application.content.handlers.list_subjects import handle_list_subjects
from src.application.content.handlers.list_tests import handle_list_tests
from src.application.content.handlers.list_topics import handle_list_topics
from src.application.content.handlers.update_micro_skill import (
    handle_update_micro_skill,
)
from src.application.content.queries.get_test_by_id import GetTestByIdQuery
from src.application.content.queries.list_micro_skills import ListMicroSkillsQuery
from src.application.content.queries.list_subjects import ListSubjectsQuery
from src.application.content.queries.list_tests import ListTestsQuery
from src.application.content.queries.list_topics import ListTopicsQuery
from src.application.delivery.commands.assign_test import AssignTestCommand
from src.application.delivery.handlers.assign_test import handle_assign_test
from src.application.ports.fixture_cleanup import (
    FixtureCleanupExecution,
    FixtureCleanupService,
)
from src.application.ports.unit_of_work import UnitOfWork
from src.application.reporting.handlers.get_child_diagnostics import (
    handle_get_child_diagnostics,
)
from src.application.reporting.handlers.get_child_results import (
    ChildResults,
    handle_get_child_results,
)
from src.application.reporting.handlers.get_child_skill_results import (
    ChildSkillResults,
    handle_get_child_skill_results,
)
from src.application.reporting.queries.get_child_diagnostics import (
    GetChildDiagnosticsQuery,
)
from src.application.reporting.queries.get_child_results import GetChildResultsQuery
from src.application.reporting.queries.get_child_skill_results import (
    GetChildSkillResultsQuery,
)
from src.domain.content.micro_skill.entity import MicroSkillNode
from src.domain.content.subject.entity import Subject
from src.domain.content.test.entity import AssessmentTest
from src.domain.content.topic.entity import Topic
from src.domain.delivery.assignment.entity import AssignmentAggregate
from src.domain.shared.statuses import CriticalityLevel, MicroSkillStatus


class AssessmentAdminFacade:
    """
    Фасад application-слоя для admin сценариев assessment-service.
    """

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        fixture_cleanup_service: FixtureCleanupService,
    ) -> None:
        self._uow = uow
        self._fixture_cleanup_service = fixture_cleanup_service

    def import_content(self, *, command: ImportContentCommand) -> ImportContentResult:
        return handle_import_content(command, uow=self._uow)

    def create_subject(self, *, code: str, name: str) -> Subject:
        return handle_create_subject(
            CreateSubjectCommand(code=code, name=name),
            uow=self._uow,
        )

    def list_subjects(self) -> list[Subject]:
        return handle_list_subjects(ListSubjectsQuery(), uow=self._uow)

    def create_topic(
        self, *, code: str, subject_code: str, grade: int, name: str
    ) -> Topic:
        return handle_create_topic(
            CreateTopicCommand(
                code=code,
                subject_code=subject_code,
                grade=grade,
                name=name,
            ),
            uow=self._uow,
        )

    def list_topics(self) -> list[Topic]:
        return handle_list_topics(ListTopicsQuery(), uow=self._uow)

    def create_micro_skill(
        self,
        *,
        node_id: str,
        subject_code: str,
        topic_code: str,
        grade: int,
        section_code: str,
        section_name: str,
        micro_skill_name: str,
        predecessor_ids: list[str],
        criticality: CriticalityLevel,
        source_ref: str | None,
        description: str | None,
        status: MicroSkillStatus | None,
        external_ref: str | None,
    ) -> MicroSkillNode:
        return handle_create_micro_skill(
            CreateMicroSkillCommand(
                node_id=node_id,
                subject_code=subject_code,
                topic_code=topic_code,
                grade=grade,
                section_code=section_code,
                section_name=section_name,
                micro_skill_name=micro_skill_name,
                predecessor_ids=predecessor_ids,
                criticality=criticality,
                source_ref=source_ref,
                description=description,
                status=status or MicroSkillStatus.ACTIVE,
                external_ref=external_ref,
            ),
            uow=self._uow,
        )

    def update_micro_skill(
        self,
        *,
        node_id: str,
        subject_code: str,
        topic_code: str,
        grade: int,
        section_code: str,
        section_name: str,
        micro_skill_name: str,
        predecessor_ids: list[str],
        criticality: CriticalityLevel,
        source_ref: str | None,
        description: str | None,
        status: MicroSkillStatus | None,
        external_ref: str | None,
    ) -> MicroSkillNode:
        return handle_update_micro_skill(
            UpdateMicroSkillCommand(
                node_id=node_id,
                subject_code=subject_code,
                topic_code=topic_code,
                grade=grade,
                section_code=section_code,
                section_name=section_name,
                micro_skill_name=micro_skill_name,
                predecessor_ids=predecessor_ids,
                criticality=criticality,
                source_ref=source_ref,
                description=description,
                status=status or MicroSkillStatus.ACTIVE,
                external_ref=external_ref,
            ),
            uow=self._uow,
        )

    def delete_micro_skill(self, *, node_id: str) -> None:
        handle_delete_micro_skill(
            DeleteMicroSkillCommand(node_id=node_id),
            uow=self._uow,
        )

    def link_micro_skill_predecessors(
        self, *, node_id: str, predecessor_ids: list[str]
    ) -> MicroSkillNode:
        return handle_link_micro_skill_predecessors(
            LinkMicroSkillPredecessorsCommand(
                node_id=node_id,
                predecessor_ids=predecessor_ids,
            ),
            uow=self._uow,
        )

    def list_micro_skills(self) -> list[MicroSkillWithBlocks]:
        return handle_list_micro_skills(ListMicroSkillsQuery(), uow=self._uow)

    def create_test(
        self,
        *,
        subject_code: str,
        grade: int,
        questions: list[QuestionInput],
    ) -> AssessmentTest:
        return handle_create_test(
            CreateTestCommand(
                subject_code=subject_code,
                grade=grade,
                questions=questions,
            ),
            uow=self._uow,
        )

    def list_tests(self) -> list[AssessmentTest]:
        return handle_list_tests(ListTestsQuery(), uow=self._uow)

    def get_test_by_id(self, *, test_id: UUID) -> AssessmentTest | None:
        return handle_get_test_by_id(GetTestByIdQuery(test_id=test_id), uow=self._uow)

    def assign_test(
        self, *, test_id: UUID, child_id: UUID, retake: bool
    ) -> AssignmentAggregate:
        return handle_assign_test(
            AssignTestCommand(test_id=test_id, child_id=child_id, retake=retake),
            uow=self._uow,
        )

    def get_child_diagnostics(self, *, child_id: UUID) -> dict[str, int]:
        return handle_get_child_diagnostics(
            GetChildDiagnosticsQuery(child_id=child_id),
            uow=self._uow,
        )

    def get_child_results(self, *, child_id: UUID) -> ChildResults:
        return handle_get_child_results(
            GetChildResultsQuery(child_id=child_id),
            uow=self._uow,
        )

    def get_child_skill_results(self, *, child_id: UUID) -> ChildSkillResults:
        return handle_get_child_skill_results(
            GetChildSkillResultsQuery(child_id=child_id),
            uow=self._uow,
        )

    def cleanup_fixtures(
        self,
        *,
        dry_run: bool,
        subject_code_patterns: tuple[str, ...],
        topic_code_patterns: tuple[str, ...],
        node_id_patterns: tuple[str, ...],
    ) -> FixtureCleanupExecution:
        return handle_cleanup_fixtures(
            CleanupFixturesCommand(
                dry_run=dry_run,
                subject_code_patterns=subject_code_patterns,
                topic_code_patterns=topic_code_patterns,
                node_id_patterns=node_id_patterns,
            ),
            uow=self._uow,
            service=self._fixture_cleanup_service,
        )
