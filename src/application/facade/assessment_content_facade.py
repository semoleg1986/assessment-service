from __future__ import annotations

from uuid import UUID

from src.application.content.commands.cleanup_fixtures import CleanupFixturesCommand
from src.application.content.commands.create_micro_skill import CreateMicroSkillCommand
from src.application.content.commands.create_subject import CreateSubjectCommand
from src.application.content.commands.create_test import (
    CreateTestCommand,
    QuestionInput,
    QuestionOptionInput,
    TextDistractorInput,
)
from src.application.content.commands.create_topic import CreateTopicCommand
from src.application.content.commands.delete_micro_skill import DeleteMicroSkillCommand
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
from src.domain.content.micro_skill.entity import MicroSkillNode
from src.domain.content.subject.entity import Subject
from src.domain.content.test.entity import AssessmentTest
from src.domain.content.topic.entity import Topic
from src.domain.delivery.assignment.entity import AssignmentAggregate
from src.domain.shared.statuses import MicroSkillStatus
from src.application.facade.inputs import (
    AssignTestInput,
    CleanupFixturesInput,
    CreateSubjectInput,
    CreateTestInput,
    CreateTopicInput,
    LinkMicroSkillPredecessorsInput,
    UpsertMicroSkillInput,
)


class AssessmentContentFacade:
    """Фасад application-слоя для CRUD/assignment/maintenance контекста."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        fixture_cleanup_service: FixtureCleanupService,
    ) -> None:
        self._uow = uow
        self._fixture_cleanup_service = fixture_cleanup_service

    def create_subject(self, *, payload: CreateSubjectInput) -> Subject:
        return handle_create_subject(
            CreateSubjectCommand(code=payload.code, name=payload.name),
            uow=self._uow,
        )

    def list_subjects(self) -> list[Subject]:
        return handle_list_subjects(ListSubjectsQuery(), uow=self._uow)

    def create_topic(self, *, payload: CreateTopicInput) -> Topic:
        return handle_create_topic(
            CreateTopicCommand(
                code=payload.code,
                subject_code=payload.subject_code,
                grade=payload.grade,
                name=payload.name,
            ),
            uow=self._uow,
        )

    def list_topics(self) -> list[Topic]:
        return handle_list_topics(ListTopicsQuery(), uow=self._uow)

    def create_micro_skill(
        self,
        *,
        payload: UpsertMicroSkillInput,
    ) -> MicroSkillNode:
        return handle_create_micro_skill(
            CreateMicroSkillCommand(
                node_id=payload.node_id,
                subject_code=payload.subject_code,
                topic_code=payload.topic_code,
                grade=payload.grade,
                section_code=payload.section_code,
                section_name=payload.section_name,
                micro_skill_name=payload.micro_skill_name,
                predecessor_ids=payload.predecessor_ids,
                criticality=payload.criticality,
                source_ref=payload.source_ref,
                description=payload.description,
                status=payload.status or MicroSkillStatus.ACTIVE,
                external_ref=payload.external_ref,
            ),
            uow=self._uow,
        )

    def update_micro_skill(
        self,
        *,
        payload: UpsertMicroSkillInput,
    ) -> MicroSkillNode:
        return handle_update_micro_skill(
            UpdateMicroSkillCommand(
                node_id=payload.node_id,
                subject_code=payload.subject_code,
                topic_code=payload.topic_code,
                grade=payload.grade,
                section_code=payload.section_code,
                section_name=payload.section_name,
                micro_skill_name=payload.micro_skill_name,
                predecessor_ids=payload.predecessor_ids,
                criticality=payload.criticality,
                source_ref=payload.source_ref,
                description=payload.description,
                status=payload.status or MicroSkillStatus.ACTIVE,
                external_ref=payload.external_ref,
            ),
            uow=self._uow,
        )

    def delete_micro_skill(self, *, node_id: str) -> None:
        handle_delete_micro_skill(
            DeleteMicroSkillCommand(node_id=node_id),
            uow=self._uow,
        )

    def link_micro_skill_predecessors(
        self, *, payload: LinkMicroSkillPredecessorsInput
    ) -> MicroSkillNode:
        return handle_link_micro_skill_predecessors(
            LinkMicroSkillPredecessorsCommand(
                node_id=payload.node_id,
                predecessor_ids=payload.predecessor_ids,
            ),
            uow=self._uow,
        )

    def list_micro_skills(self) -> list[MicroSkillWithBlocks]:
        return handle_list_micro_skills(ListMicroSkillsQuery(), uow=self._uow)

    def create_test(
        self,
        *,
        payload: CreateTestInput,
    ) -> AssessmentTest:
        mapped_questions = [
            QuestionInput(
                node_id=question.node_id,
                text=question.text,
                question_type=question.question_type,
                answer_key=question.answer_key,
                correct_option_id=question.correct_option_id,
                options=[
                    QuestionOptionInput(
                        option_id=option.option_id,
                        text=option.text,
                        position=option.position,
                        diagnostic_tag=option.diagnostic_tag,
                    )
                    for option in question.options
                ],
                text_distractors=[
                    TextDistractorInput(
                        pattern=item.pattern,
                        match_mode=item.match_mode,
                        diagnostic_tag=item.diagnostic_tag,
                    )
                    for item in question.text_distractors
                ],
                max_score=question.max_score,
            )
            for question in payload.questions
        ]
        return handle_create_test(
            CreateTestCommand(
                subject_code=payload.subject_code,
                grade=payload.grade,
                questions=mapped_questions,
            ),
            uow=self._uow,
        )

    def list_tests(self) -> list[AssessmentTest]:
        return handle_list_tests(ListTestsQuery(), uow=self._uow)

    def get_test_by_id(self, *, test_id: UUID) -> AssessmentTest | None:
        return handle_get_test_by_id(GetTestByIdQuery(test_id=test_id), uow=self._uow)

    def assign_test(self, *, payload: AssignTestInput) -> AssignmentAggregate:
        return handle_assign_test(
            AssignTestCommand(
                test_id=payload.test_id,
                child_id=payload.child_id,
                retake=payload.retake,
            ),
            uow=self._uow,
        )

    def cleanup_fixtures(
        self,
        *,
        payload: CleanupFixturesInput,
    ) -> FixtureCleanupExecution:
        return handle_cleanup_fixtures(
            CleanupFixturesCommand(
                dry_run=payload.dry_run,
                subject_code_patterns=payload.subject_code_patterns,
                topic_code_patterns=payload.topic_code_patterns,
                node_id_patterns=payload.node_id_patterns,
            ),
            uow=self._uow,
            service=self._fixture_cleanup_service,
        )
