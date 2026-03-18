from __future__ import annotations

from uuid import UUID, uuid4

from src.application.facade import (
    AssessmentContentFacade,
    AssessmentImportFacade,
    AssessmentResultsFacade,
    AssessmentUserFacade,
    SubmittedAnswerData,
    TestQuestionData as _TestQuestionData,
    TestTextDistractorData as _TestTextDistractorData,
)
from src.application.ports.fixture_cleanup import (
    FixtureCleanupCounts,
    FixtureCleanupExecution,
    FixtureCleanupFilters,
    FixtureCleanupService,
)
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.shared.questions import DiagnosticTag, QuestionType, TextMatchMode
from src.domain.shared.statuses import CriticalityLevel, MicroSkillStatus
from src.infrastructure.uow import InMemoryUnitOfWork


class _NoopFixtureCleanupService(FixtureCleanupService):
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


def _build_content_facade(uow: InMemoryUnitOfWork) -> AssessmentContentFacade:
    return AssessmentContentFacade(
        uow=uow,
        fixture_cleanup_service=_NoopFixtureCleanupService(),
    )


def _seed_basic_catalog(
    facade: AssessmentContentFacade,
) -> tuple[UUID, UUID]:
    facade.create_subject(code="math", name="Math")
    facade.create_topic(
        code="MATH-T1",
        subject_code="math",
        grade=1,
        name="Numbers",
    )
    facade.create_micro_skill(
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

    test = facade.create_test(
        subject_code="math",
        grade=1,
        questions=[
            _TestQuestionData(
                node_id="MATH-N1",
                text="2 + 2 = ?",
                question_type=QuestionType.TEXT,
                answer_key="4",
                correct_option_id=None,
                options=[],
                text_distractors=[
                    _TestTextDistractorData(
                        pattern="5",
                        match_mode=TextMatchMode.EXACT,
                        diagnostic_tag=DiagnosticTag.INATTENTION,
                    )
                ],
                max_score=1,
            )
        ],
    )

    child_id = uuid4()
    assignment = facade.assign_test(
        test_id=test.test_id,
        child_id=child_id,
        retake=False,
    )
    return assignment.assignment_id, child_id


def test_content_facade_contract() -> None:
    uow = InMemoryUnitOfWork()
    facade = _build_content_facade(uow)

    assignment_id, child_id = _seed_basic_catalog(facade)

    assert len(facade.list_subjects()) == 1
    assert len(facade.list_topics()) == 1
    assert len(facade.list_micro_skills()) == 1
    assert len(facade.list_tests()) == 1

    assignments = uow.assignments.list_by_child(child_id)
    assert assignments[0].assignment_id == assignment_id

    cleanup_result = facade.cleanup_fixtures(
        dry_run=True,
        subject_code_patterns=("^math$",),
        topic_code_patterns=("^MATH",),
        node_id_patterns=("^MATH",),
    )
    assert cleanup_result.dry_run is True


def test_import_facade_contract() -> None:
    uow = InMemoryUnitOfWork()
    facade = AssessmentImportFacade(uow=uow)

    payload = {
        "subjects": [{"code": "imp_math", "name": "Import Math"}],
        "topics": [
            {
                "code": "IMP-T1",
                "subject_code": "imp_math",
                "grade": 1,
                "name": "Topic",
            }
        ],
        "micro_skills": [
            {
                "node_id": "IMP-N1",
                "subject_code": "imp_math",
                "topic_code": "IMP-T1",
                "grade": 1,
                "section_code": "R1",
                "section_name": "Section",
                "micro_skill_name": "Skill",
                "predecessor_ids": [],
                "criticality": CriticalityLevel.MEDIUM,
                "source_ref": "tests",
                "status": MicroSkillStatus.ACTIVE,
            }
        ],
        "tests": [],
    }

    validated = facade.import_content_payload(
        source_id="facade-contract",
        contract_version="v1.2",
        validate_only=True,
        error_mode="collect",
        payload=payload,
    )
    assert validated.status in {"validated", "validated_with_errors"}
    assert validated.errors == []

    applied = facade.import_content_payload(
        source_id="facade-contract",
        contract_version="v1.2",
        validate_only=False,
        error_mode="collect",
        payload=payload,
    )
    assert applied.status in {"completed", "completed_with_errors"}
    assert applied.errors == []
    assert applied.imported == 3

    idempotent = facade.import_content_payload(
        source_id="facade-contract",
        contract_version="v1.2",
        validate_only=False,
        error_mode="collect",
        payload=payload,
    )
    assert idempotent.status in {"completed", "completed_with_errors"}
    assert idempotent.errors == []
    assert idempotent.imported == 0


def test_user_and_results_facades_contract() -> None:
    uow = InMemoryUnitOfWork()
    content = _build_content_facade(uow)
    assignment_id, child_id = _seed_basic_catalog(content)

    user = AssessmentUserFacade(uow=uow)
    results = AssessmentResultsFacade(uow=uow)

    assignments = user.list_assignments_by_child(child_id=child_id)
    assert len(assignments) == 1

    attempt = user.start_attempt(assignment_id=assignment_id, child_id=child_id)
    save_result = user.save_attempt_answers(
        attempt_id=attempt.attempt_id,
        answers=[
            SubmittedAnswerData(
                question_id=content.list_tests()[0].questions[0].question_id,
                value="4",
                selected_option_id=None,
                time_spent_ms=1200,
            )
        ],
    )
    assert int(save_result["saved_answers"]) == 1

    submit = user.submit_attempt(
        attempt_id=attempt.attempt_id,
        answers=[
            SubmittedAnswerData(
                question_id=content.list_tests()[0].questions[0].question_id,
                value="4",
                selected_option_id=None,
                time_spent_ms=1200,
            )
        ],
    )
    assert submit["score"] == 1

    attempt_result = user.get_attempt_result(attempt_id=attempt.attempt_id)
    assert attempt_result["status"] == "submitted"
    assert len(attempt_result["answers"]) == 1

    child_results = results.get_child_results(child_id=child_id)
    assert child_results["summary"]["attempts_total"] == 1
    assert child_results["summary"]["correct_answers_total"] == 1

    diagnostics = results.get_child_diagnostics(child_id=child_id)
    assert diagnostics["attempts_total"] == 1

    skill_results = results.get_child_skill_results(child_id=child_id)
    assert skill_results["summary"]["total_skills"] >= 1
