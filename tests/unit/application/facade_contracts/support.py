from __future__ import annotations

from uuid import UUID, uuid4

from src.application.facade import (
    AssignTestInput,
    AssessmentContentFacade,
    CreateSubjectInput,
    CreateTestInput,
    CreateTopicInput,
    TestQuestionData as TestQuestionDataInput,
    TestTextDistractorData as TestTextDistractorDataInput,
    UpsertMicroSkillInput,
)
from src.application.ports.fixture_cleanup import (
    FixtureCleanupCounts,
    FixtureCleanupExecution,
    FixtureCleanupFilters,
    FixtureCleanupService,
)
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.shared.questions import DiagnosticTag, QuestionType, TextMatchMode
from src.domain.shared.statuses import CriticalityLevel
from src.infrastructure.uow import InMemoryUnitOfWork


class NoopFixtureCleanupService(FixtureCleanupService):
    def run(
        self,
        *,
        uow: UnitOfWork,
        dry_run: bool,
        filters: FixtureCleanupFilters,
    ) -> FixtureCleanupExecution:
        del uow
        return FixtureCleanupExecution(
            dry_run=dry_run,
            filters=filters,
            matched=FixtureCleanupCounts(),
            deleted=FixtureCleanupCounts(),
        )


def build_content_facade(uow: InMemoryUnitOfWork) -> AssessmentContentFacade:
    return AssessmentContentFacade(
        uow=uow,
        fixture_cleanup_service=NoopFixtureCleanupService(),
    )


def seed_basic_catalog(facade: AssessmentContentFacade) -> tuple[UUID, UUID]:
    facade.create_subject(payload=CreateSubjectInput(code="math", name="Math"))
    facade.create_topic(
        payload=CreateTopicInput(
            code="MATH-T1",
            subject_code="math",
            grade=1,
            name="Numbers",
        )
    )
    facade.create_micro_skill(
        payload=UpsertMicroSkillInput(
            node_id="MATH-N1",
            subject_code="math",
            topic_code="MATH-T1",
            grade=1,
            section_code="R1",
            section_name="Section",
            micro_skill_name="Add numbers",
            predecessor_ids=[],
            criticality=CriticalityLevel.MEDIUM,
            source_ref="tests",
            description=None,
            status=None,
            external_ref=None,
        )
    )
    test = facade.create_test(
        payload=CreateTestInput(
            subject_code="math",
            grade=1,
            questions=[
                TestQuestionDataInput(
                    node_id="MATH-N1",
                    text="2 + 2 = ?",
                    question_type=QuestionType.TEXT,
                    answer_key="4",
                    correct_option_id=None,
                    options=[],
                    text_distractors=[
                        TestTextDistractorDataInput(
                            pattern="5",
                            match_mode=TextMatchMode.EXACT,
                            diagnostic_tag=DiagnosticTag.INATTENTION,
                        )
                    ],
                    max_score=1,
                )
            ],
        ),
    )
    child_id = uuid4()
    assignment = facade.assign_test(
        payload=AssignTestInput(test_id=test.test_id, child_id=child_id, retake=False)
    )
    return assignment.assignment_id, child_id
