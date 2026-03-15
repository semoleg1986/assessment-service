from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status

from src.application.commands import (
    AssignTestCommand,
    CleanupFixturesCommand,
    CreateMicroSkillCommand,
    CreateSubjectCommand,
    CreateTestCommand,
    CreateTopicCommand,
    DeleteMicroSkillCommand,
    LinkMicroSkillPredecessorsCommand,
    QuestionInput,
    QuestionOptionInput,
    TextDistractorInput,
    UpdateMicroSkillCommand,
)
from src.application.handlers import (
    handle_assign_test,
    handle_cleanup_fixtures,
    handle_create_micro_skill,
    handle_create_subject,
    handle_create_test,
    handle_create_topic,
    handle_delete_micro_skill,
    handle_get_child_diagnostics,
    handle_get_child_results,
    handle_get_child_skill_results,
    handle_get_test_by_id,
    handle_link_micro_skill_predecessors,
    handle_list_micro_skills,
    handle_list_subjects,
    handle_list_tests,
    handle_list_topics,
    handle_update_micro_skill,
)
from src.application.ports.fixture_cleanup import (
    FixtureCleanupService,
    FixtureCleanupUnsupportedError,
)
from src.application.ports.unit_of_work import UnitOfWork
from src.application.queries import (
    GetChildDiagnosticsQuery,
    GetChildResultsQuery,
    GetChildSkillResultsQuery,
    GetTestByIdQuery,
    ListMicroSkillsQuery,
    ListSubjectsQuery,
    ListTestsQuery,
    ListTopicsQuery,
)
from src.domain.errors import InvariantViolationError, NotFoundError
from src.domain.shared.questions import DiagnosticTag
from src.interface.http.v1.content_import import import_content_with_uow
from src.interface.http.v1.schemas import (
    AssignmentResponse,
    AssignTestRequest,
    ChildDiagnosticsResponse,
    ChildResultsAttemptResponse,
    ChildResultsDiagnosticTagCountResponse,
    ChildResultsResponse,
    ChildResultsSummaryResponse,
    ChildSkillResultResponse,
    ChildSkillResultsResponse,
    ChildSkillResultsSummaryResponse,
    ContentImportRequest,
    ContentImportResponse,
    CreateTestRequest,
    FixtureCleanupCountsResponse,
    FixtureCleanupFiltersResponse,
    FixtureCleanupRequest,
    FixtureCleanupResponse,
    MicroSkillCreateRequest,
    MicroSkillLinkRequest,
    MicroSkillResponse,
    MicroSkillUpdateRequest,
    PublishTestResponse,
    QuestionOptionResponse,
    QuestionResponse,
    SubjectCreateRequest,
    SubjectResponse,
    TestResponse,
    TopicCreateRequest,
    TopicResponse,
)

router = APIRouter(tags=["assessment"], route_class=DishkaRoute)


def _sorted_diagnostic_tag_counts(
    counts: dict[str, int],
) -> list[ChildResultsDiagnosticTagCountResponse]:
    return [
        ChildResultsDiagnosticTagCountResponse(tag=DiagnosticTag(tag), count=count)
        for tag, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]


@router.post(
    "/admin/content/import",
    response_model=ContentImportResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def import_content(
    body: ContentImportRequest,
    uow: FromDishka[UnitOfWork],
) -> ContentImportResponse:
    return import_content_with_uow(body=body, current_uow=uow)


def _cleanup_counts_response(
    *,
    subjects: int,
    topics: int,
    micro_skills: int,
    tests: int,
    questions: int,
    assignments: int,
    attempts: int,
    answers: int,
) -> FixtureCleanupCountsResponse:
    return FixtureCleanupCountsResponse(
        subjects=subjects,
        topics=topics,
        micro_skills=micro_skills,
        tests=tests,
        questions=questions,
        assignments=assignments,
        attempts=attempts,
        answers=answers,
    )


@router.post(
    "/admin/fixtures/cleanup",
    response_model=FixtureCleanupResponse,
    status_code=status.HTTP_200_OK,
)
def cleanup_fixtures(
    body: FixtureCleanupRequest,
    uow: FromDishka[UnitOfWork],
    fixture_cleanup_service: FromDishka[FixtureCleanupService],
) -> FixtureCleanupResponse:
    try:
        result = handle_cleanup_fixtures(
            CleanupFixturesCommand(
                dry_run=body.dry_run,
                subject_code_patterns=tuple(body.subject_code_patterns),
                topic_code_patterns=tuple(body.topic_code_patterns),
                node_id_patterns=tuple(body.node_id_patterns),
            ),
            uow=uow,
            service=fixture_cleanup_service,
        )
    except FixtureCleanupUnsupportedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return FixtureCleanupResponse(
        status="planned" if result.dry_run else "completed",
        dry_run=result.dry_run,
        filters=FixtureCleanupFiltersResponse(
            subject_code_patterns=list(result.filters.subject_code_patterns),
            topic_code_patterns=list(result.filters.topic_code_patterns),
            node_id_patterns=list(result.filters.node_id_patterns),
        ),
        matched=_cleanup_counts_response(
            subjects=result.matched.subjects,
            topics=result.matched.topics,
            micro_skills=result.matched.micro_skills,
            tests=result.matched.tests,
            questions=result.matched.questions,
            assignments=result.matched.assignments,
            attempts=result.matched.attempts,
            answers=result.matched.answers,
        ),
        deleted=_cleanup_counts_response(
            subjects=result.deleted.subjects,
            topics=result.deleted.topics,
            micro_skills=result.deleted.micro_skills,
            tests=result.deleted.tests,
            questions=result.deleted.questions,
            assignments=result.deleted.assignments,
            attempts=result.deleted.attempts,
            answers=result.deleted.answers,
        ),
    )


@router.post("/tests", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
@router.post(
    "/admin/tests",
    response_model=TestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_test(
    body: CreateTestRequest,
    uow: FromDishka[UnitOfWork],
) -> TestResponse:
    try:
        test = handle_create_test(
            CreateTestCommand(
                subject_code=body.subject_code,
                grade=body.grade,
                questions=[
                    QuestionInput(
                        node_id=q.node_id,
                        text=q.text,
                        question_type=q.question_type,
                        answer_key=q.answer_key,
                        correct_option_id=q.correct_option_id,
                        options=[
                            QuestionOptionInput(
                                option_id=option.option_id,
                                text=option.text,
                                position=option.position,
                                diagnostic_tag=option.diagnostic_tag,
                            )
                            for option in q.options
                        ],
                        text_distractors=[
                            TextDistractorInput(
                                pattern=distractor.pattern,
                                match_mode=distractor.match_mode,
                                diagnostic_tag=distractor.diagnostic_tag,
                            )
                            for distractor in q.text_distractors
                        ],
                        max_score=q.max_score,
                    )
                    for q in body.questions
                ],
            ),
            uow=uow,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return TestResponse(
        test_id=test.test_id,
        subject_code=test.subject_code,
        grade=test.grade,
        version=test.version,
        questions=[
            QuestionResponse(
                question_id=q.question_id,
                node_id=q.node_id,
                text=q.text,
                question_type=q.question_type,
                max_score=q.max_score,
                options=[
                    QuestionOptionResponse(
                        option_id=option.option_id,
                        text=option.text,
                        position=option.position,
                    )
                    for option in sorted(q.options, key=lambda item: item.position)
                ],
            )
            for q in test.questions
        ],
    )


@router.get("/tests", response_model=list[TestResponse])
@router.get("/admin/tests", response_model=list[TestResponse])
def list_tests(
    uow: FromDishka[UnitOfWork],
) -> list[TestResponse]:
    tests = handle_list_tests(ListTestsQuery(), uow=uow)
    return [
        TestResponse(
            test_id=t.test_id,
            subject_code=t.subject_code,
            grade=t.grade,
            version=t.version,
            questions=[
                QuestionResponse(
                    question_id=q.question_id,
                    node_id=q.node_id,
                    text=q.text,
                    question_type=q.question_type,
                    max_score=q.max_score,
                    options=[
                        QuestionOptionResponse(
                            option_id=option.option_id,
                            text=option.text,
                            position=option.position,
                        )
                        for option in sorted(q.options, key=lambda item: item.position)
                    ],
                )
                for q in t.questions
            ],
        )
        for t in tests
    ]


@router.post(
    "/admin/tests/{test_id}/publish",
    response_model=PublishTestResponse,
)
def publish_test(
    test_id: UUID,
    uow: FromDishka[UnitOfWork],
) -> PublishTestResponse:
    if handle_get_test_by_id(GetTestByIdQuery(test_id=test_id), uow=uow) is None:
        raise HTTPException(status_code=404, detail="test not found")
    return PublishTestResponse(test_id=test_id, status="published")


@router.post(
    "/admin/subjects",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subject(
    body: SubjectCreateRequest,
    uow: FromDishka[UnitOfWork],
) -> SubjectResponse:
    try:
        subject = handle_create_subject(
            CreateSubjectCommand(code=body.code, name=body.name), uow=uow
        )
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return SubjectResponse(code=subject.code, name=subject.name)


@router.get("/admin/subjects", response_model=list[SubjectResponse])
def list_subjects(
    uow: FromDishka[UnitOfWork],
) -> list[SubjectResponse]:
    subjects = handle_list_subjects(ListSubjectsQuery(), uow=uow)
    return [SubjectResponse(code=s.code, name=s.name) for s in subjects]


@router.post(
    "/admin/topics",
    response_model=TopicResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_topic(
    body: TopicCreateRequest,
    uow: FromDishka[UnitOfWork],
) -> TopicResponse:
    try:
        topic = handle_create_topic(
            CreateTopicCommand(
                code=body.code,
                subject_code=body.subject_code,
                grade=body.grade,
                name=body.name,
            ),
            uow=uow,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return TopicResponse(
        code=topic.code,
        subject_code=topic.subject_code,
        grade=topic.grade,
        name=topic.name,
    )


@router.get("/admin/topics", response_model=list[TopicResponse])
def list_topics(
    uow: FromDishka[UnitOfWork],
) -> list[TopicResponse]:
    topics = handle_list_topics(ListTopicsQuery(), uow=uow)
    return [
        TopicResponse(
            code=t.code,
            subject_code=t.subject_code,
            grade=t.grade,
            name=t.name,
        )
        for t in topics
    ]


@router.post(
    "/admin/micro-skills",
    response_model=MicroSkillResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_micro_skill(
    body: MicroSkillCreateRequest,
    uow: FromDishka[UnitOfWork],
) -> MicroSkillResponse:
    try:
        node = handle_create_micro_skill(
            CreateMicroSkillCommand(
                node_id=body.node_id,
                subject_code=body.subject_code,
                topic_code=body.topic_code,
                grade=body.grade,
                section_code=body.section_code,
                section_name=body.section_name,
                micro_skill_name=body.micro_skill_name,
                predecessor_ids=body.predecessor_ids,
                criticality=body.criticality,
                source_ref=body.source_ref,
                description=body.description,
                status=body.status,
                external_ref=body.external_ref,
            ),
            uow=uow,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return MicroSkillResponse(
        node_id=node.node_id,
        subject_code=node.subject_code,
        topic_code=node.topic_code,
        grade=node.grade,
        section_code=node.section_code,
        section_name=node.section_name,
        micro_skill_name=node.micro_skill_name,
        predecessor_ids=node.predecessor_ids,
        criticality=node.criticality,
        source_ref=node.source_ref,
        description=node.description,
        status=node.status,
        external_ref=node.external_ref,
        version=node.version,
        created_at=node.created_at,
        updated_at=node.updated_at,
        blocks_count=0,
    )


@router.put(
    "/admin/micro-skills/{node_id}",
    response_model=MicroSkillResponse,
)
def update_micro_skill(
    node_id: str,
    body: MicroSkillUpdateRequest,
    uow: FromDishka[UnitOfWork],
) -> MicroSkillResponse:
    try:
        node = handle_update_micro_skill(
            UpdateMicroSkillCommand(
                node_id=node_id,
                subject_code=body.subject_code,
                topic_code=body.topic_code,
                grade=body.grade,
                section_code=body.section_code,
                section_name=body.section_name,
                micro_skill_name=body.micro_skill_name,
                predecessor_ids=body.predecessor_ids,
                criticality=body.criticality,
                source_ref=body.source_ref,
                description=body.description,
                status=body.status,
                external_ref=body.external_ref,
            ),
            uow=uow,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    blocks_count = next(
        (
            x["blocks_count"]
            for x in handle_list_micro_skills(ListMicroSkillsQuery(), uow=uow)
            if x["node"].node_id == node.node_id
        ),
        0,
    )
    return MicroSkillResponse(
        node_id=node.node_id,
        subject_code=node.subject_code,
        topic_code=node.topic_code,
        grade=node.grade,
        section_code=node.section_code,
        section_name=node.section_name,
        micro_skill_name=node.micro_skill_name,
        predecessor_ids=node.predecessor_ids,
        criticality=node.criticality,
        source_ref=node.source_ref,
        description=node.description,
        status=node.status,
        external_ref=node.external_ref,
        version=node.version,
        created_at=node.created_at,
        updated_at=node.updated_at,
        blocks_count=blocks_count,
    )


@router.delete(
    "/admin/micro-skills/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_micro_skill(
    node_id: str,
    uow: FromDishka[UnitOfWork],
) -> None:
    try:
        handle_delete_micro_skill(
            DeleteMicroSkillCommand(node_id=node_id),
            uow=uow,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/admin/micro-skills/{node_id}/links",
    response_model=MicroSkillResponse,
)
def link_micro_skill_predecessors(
    node_id: str,
    body: MicroSkillLinkRequest,
    uow: FromDishka[UnitOfWork],
) -> MicroSkillResponse:
    try:
        node = handle_link_micro_skill_predecessors(
            LinkMicroSkillPredecessorsCommand(
                node_id=node_id,
                predecessor_ids=body.predecessor_ids,
            ),
            uow=uow,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    blocks_count = next(
        (
            x["blocks_count"]
            for x in handle_list_micro_skills(ListMicroSkillsQuery(), uow=uow)
            if x["node"].node_id == node.node_id
        ),
        0,
    )
    return MicroSkillResponse(
        node_id=node.node_id,
        subject_code=node.subject_code,
        topic_code=node.topic_code,
        grade=node.grade,
        section_code=node.section_code,
        section_name=node.section_name,
        micro_skill_name=node.micro_skill_name,
        predecessor_ids=node.predecessor_ids,
        criticality=node.criticality,
        source_ref=node.source_ref,
        description=node.description,
        status=node.status,
        external_ref=node.external_ref,
        version=node.version,
        created_at=node.created_at,
        updated_at=node.updated_at,
        blocks_count=blocks_count,
    )


@router.get("/admin/micro-skills", response_model=list[MicroSkillResponse])
def list_micro_skills(
    uow: FromDishka[UnitOfWork],
) -> list[MicroSkillResponse]:
    nodes = handle_list_micro_skills(ListMicroSkillsQuery(), uow=uow)
    return [
        MicroSkillResponse(
            node_id=item["node"].node_id,
            subject_code=item["node"].subject_code,
            topic_code=item["node"].topic_code,
            grade=item["node"].grade,
            section_code=item["node"].section_code,
            section_name=item["node"].section_name,
            micro_skill_name=item["node"].micro_skill_name,
            predecessor_ids=item["node"].predecessor_ids,
            criticality=item["node"].criticality,
            source_ref=item["node"].source_ref,
            description=item["node"].description,
            status=item["node"].status,
            external_ref=item["node"].external_ref,
            version=item["node"].version,
            created_at=item["node"].created_at,
            updated_at=item["node"].updated_at,
            blocks_count=item["blocks_count"],
        )
        for item in nodes
    ]


@router.post(
    "/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/admin/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_test(
    body: AssignTestRequest,
    uow: FromDishka[UnitOfWork],
) -> AssignmentResponse:
    try:
        assignment = handle_assign_test(
            AssignTestCommand(
                test_id=body.test_id,
                child_id=body.child_id,
                retake=body.retake,
            ),
            uow=uow,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return AssignmentResponse(
        assignment_id=assignment.assignment_id,
        test_id=assignment.test_id,
        child_id=assignment.child_id,
        status=assignment.status.value,
        attempt_no=assignment.attempt_no,
    )


@router.get(
    "/admin/diagnostics/children/{child_id}",
    response_model=ChildDiagnosticsResponse,
)
def get_child_diagnostics(
    child_id: UUID,
    uow: FromDishka[UnitOfWork],
) -> ChildDiagnosticsResponse:
    result = handle_get_child_diagnostics(
        GetChildDiagnosticsQuery(child_id=child_id),
        uow=uow,
    )
    return ChildDiagnosticsResponse(
        child_id=child_id,
        assignments_total=result["assignments_total"],
        attempts_total=result["attempts_total"],
    )


@router.get(
    "/admin/results/children/{child_id}",
    response_model=ChildResultsResponse,
)
def get_child_results(
    child_id: UUID,
    uow: FromDishka[UnitOfWork],
) -> ChildResultsResponse:
    result = handle_get_child_results(
        GetChildResultsQuery(child_id=child_id),
        uow=uow,
    )
    return ChildResultsResponse(
        child_id=child_id,
        summary=ChildResultsSummaryResponse(
            attempts_total=result["summary"]["attempts_total"],
            submitted_attempts_total=result["summary"]["submitted_attempts_total"],
            started_attempts_total=result["summary"]["started_attempts_total"],
            attempts_with_diagnostics_total=(
                result["summary"]["attempts_with_diagnostics_total"]
            ),
            answers_total=result["summary"]["answers_total"],
            expected_answers_total=result["summary"]["expected_answers_total"],
            correct_answers_total=result["summary"]["correct_answers_total"],
            accuracy_percent=result["summary"]["accuracy_percent"],
            time_spent_ms_total=result["summary"]["time_spent_ms_total"],
            avg_time_per_answer_ms=result["summary"]["avg_time_per_answer_ms"],
            resolved_diagnostic_tags=_sorted_diagnostic_tag_counts(
                result["summary"]["resolved_diagnostic_tags"]
            ),
        ),
        attempts=[
            ChildResultsAttemptResponse(
                attempt_id=item["attempt_id"],
                assignment_id=item["assignment_id"],
                status=item["status"],
                score=item["score"],
                started_at=item["started_at"],
                submitted_at=item["submitted_at"],
                duration_seconds=item["duration_seconds"],
                answers_total=item["answers_total"],
                expected_answers_total=item["expected_answers_total"],
                unanswered_answers_total=item["unanswered_answers_total"],
                correct_answers=item["correct_answers"],
                accuracy_percent=item["accuracy_percent"],
                time_spent_ms_total=item["time_spent_ms_total"],
                avg_time_per_answer_ms=item["avg_time_per_answer_ms"],
                has_resolved_diagnostics=item["has_resolved_diagnostics"],
                resolved_diagnostic_tags=_sorted_diagnostic_tag_counts(
                    item["resolved_diagnostic_tags"]
                ),
            )
            for item in result["attempts"]
        ],
    )


@router.get(
    "/admin/results/children/{child_id}/skills",
    response_model=ChildSkillResultsResponse,
)
def get_child_skill_results(
    child_id: UUID,
    uow: FromDishka[UnitOfWork],
) -> ChildSkillResultsResponse:
    result = handle_get_child_skill_results(
        GetChildSkillResultsQuery(child_id=child_id),
        uow=uow,
    )
    return ChildSkillResultsResponse(
        child_id=child_id,
        summary=ChildSkillResultsSummaryResponse(
            total_skills=result["summary"]["total_skills"],
            high_gap_total=result["summary"]["high_gap_total"],
            medium_gap_total=result["summary"]["medium_gap_total"],
            low_gap_total=result["summary"]["low_gap_total"],
            insufficient_data_total=result["summary"]["insufficient_data_total"],
        ),
        skills=[
            ChildSkillResultResponse(
                node_id=item["node_id"],
                topic_code=item["topic_code"],
                skill_name=item["skill_name"],
                attempted_questions=item["attempted_questions"],
                correct_answers=item["correct_answers"],
                accuracy_percent=item["accuracy_percent"],
                avg_time_per_answer_ms=item["avg_time_per_answer_ms"],
                wilson_low=item["wilson_low"],
                wilson_high=item["wilson_high"],
                gap_level=item["gap_level"],
                resolved_diagnostic_tags=_sorted_diagnostic_tag_counts(
                    item["resolved_diagnostic_tags"]
                ),
                recommendation=item["recommendation"],
            )
            for item in result["skills"]
        ],
    )
