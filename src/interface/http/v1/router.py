from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import APIRouter, HTTPException, status

from src.application.commands import (
    AssignTestCommand,
    CreateMicroSkillCommand,
    CreateSubjectCommand,
    CreateTestCommand,
    CreateTopicCommand,
    LinkMicroSkillPredecessorsCommand,
    QuestionInput,
    StartAttemptCommand,
    SubmitAttemptCommand,
    SubmittedAnswerInput,
)
from src.application.handlers import (
    handle_assign_test,
    handle_create_micro_skill,
    handle_create_subject,
    handle_create_test,
    handle_create_topic,
    handle_get_attempt_result,
    handle_link_micro_skill_predecessors,
    handle_list_micro_skills,
    handle_list_subjects,
    handle_list_tests,
    handle_list_topics,
    handle_start_attempt,
    handle_submit_attempt,
)
from src.application.queries import (
    GetAttemptResultQuery,
    ListMicroSkillsQuery,
    ListSubjectsQuery,
    ListTestsQuery,
    ListTopicsQuery,
)
from src.domain.aggregates.test_aggregate import AssessmentTest
from src.domain.entities.micro_skill_node import MicroSkillNode
from src.domain.entities.question import Question
from src.domain.entities.subject import Subject
from src.domain.entities.topic import Topic
from src.domain.errors import InvariantViolationError, NotFoundError
from src.domain.value_objects.statuses import CriticalityLevel
from src.infrastructure.uow import build_uow
from src.interface.http.v1.schemas import (
    AssignmentListItemResponse,
    AssignmentResponse,
    AssignTestRequest,
    AttemptAnswerResponse,
    AttemptResultResponse,
    ChildDiagnosticsResponse,
    ContentImportRequest,
    ContentImportResponse,
    CreateTestRequest,
    MicroSkillCreateRequest,
    MicroSkillLinkRequest,
    MicroSkillResponse,
    PublishTestResponse,
    QuestionResponse,
    SaveAttemptAnswersRequest,
    SaveAttemptAnswersResponse,
    StartAttemptByAssignmentRequest,
    StartAttemptRequest,
    StartAttemptResponse,
    SubjectCreateRequest,
    SubjectResponse,
    SubmitAttemptRequest,
    SubmitAttemptResponse,
    TestResponse,
    TopicCreateRequest,
    TopicResponse,
)

router = APIRouter(prefix="/v1", tags=["assessment"])
uow = build_uow()


def _ensure_unique(items: list[str], *, label: str) -> None:
    if len(items) != len(set(items)):
        raise HTTPException(
            status_code=422,
            detail=f"Duplicate identifiers in import payload: {label}",
        )


@router.post(
    "/admin/content/import",
    response_model=ContentImportResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def import_content(body: ContentImportRequest) -> ContentImportResponse:
    if not body.contract_version.startswith("v1"):
        raise HTTPException(
            status_code=422,
            detail="Unsupported contract_version, expected v1*",
        )

    payload = body.payload
    _ensure_unique([s.code for s in payload.subjects], label="subjects.code")
    _ensure_unique([t.code for t in payload.topics], label="topics.code")
    _ensure_unique(
        [m.node_id for m in payload.micro_skills], label="micro_skills.node_id"
    )
    _ensure_unique([t.external_id for t in payload.tests], label="tests.external_id")
    for test in payload.tests:
        _ensure_unique(
            [q.external_id for q in test.questions],
            label=f"tests[{test.external_id}].questions.external_id",
        )

    details: dict[str, int] = {
        "subjects_created": 0,
        "subjects_updated": 0,
        "topics_created": 0,
        "topics_updated": 0,
        "micro_skills_created": 0,
        "micro_skills_updated": 0,
        "tests_created": 0,
        "tests_updated": 0,
    }

    for subject in payload.subjects:
        existing_subject = uow.subjects.get(subject.code)
        if existing_subject is None:
            details["subjects_created"] += 1
            handle_create_subject(
                CreateSubjectCommand(code=subject.code, name=subject.name), uow=uow
            )
            continue

        elif existing_subject.name != subject.name:
            details["subjects_updated"] += 1
        uow.subjects.save(
            Subject(
                code=subject.code,
                name=subject.name,
            )
        )
        uow.commit()

    for topic in payload.topics:
        if uow.subjects.get(topic.subject_code) is None:
            raise HTTPException(
                status_code=422,
                detail=f"Topic references unknown subject_code: {topic.subject_code}",
            )
        existing_topic = uow.topics.get(topic.code)
        if existing_topic is None:
            details["topics_created"] += 1
            handle_create_topic(
                CreateTopicCommand(
                    code=topic.code,
                    subject_code=topic.subject_code,
                    grade=topic.grade,
                    name=topic.name,
                ),
                uow=uow,
            )
            continue
        changed = (
            existing_topic.subject_code != topic.subject_code
            or existing_topic.grade != topic.grade
            or existing_topic.name != topic.name
        )
        if changed:
            details["topics_updated"] += 1
        uow.topics.save(
            Topic(
                code=topic.code,
                subject_code=topic.subject_code,
                grade=topic.grade,
                name=topic.name,
            )
        )
        uow.commit()

    seen_nodes: set[str] = {n.node_id for n in uow.micro_skills.list()}
    for node in payload.micro_skills:
        if uow.subjects.get(node.subject_code) is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Micro-skill references unknown subject_code: "
                    f"{node.subject_code}"
                ),
            )
        for pred in node.predecessor_ids:
            if pred not in seen_nodes:
                raise HTTPException(
                    status_code=422,
                    detail=f"Unknown predecessor_id: {pred} for node {node.node_id}",
                )

        existing_node = uow.micro_skills.get(node.node_id)
        if existing_node is None:
            details["micro_skills_created"] += 1
            handle_create_micro_skill(
                CreateMicroSkillCommand(
                    node_id=node.node_id,
                    subject_code=node.subject_code,
                    grade=node.grade,
                    section_code=node.section_code,
                    section_name=node.section_name,
                    micro_skill_name=node.micro_skill_name,
                    predecessor_ids=node.predecessor_ids,
                    criticality=node.criticality,
                    source_ref=node.source_ref,
                ),
                uow=uow,
            )
            seen_nodes.add(node.node_id)
            continue

        changed = (
            existing_node.subject_code != node.subject_code
            or existing_node.grade != node.grade
            or existing_node.section_code != node.section_code
            or existing_node.section_name != node.section_name
            or existing_node.micro_skill_name != node.micro_skill_name
            or existing_node.predecessor_ids != node.predecessor_ids
            or existing_node.criticality.value != node.criticality
            or existing_node.source_ref != node.source_ref
        )
        if changed:
            details["micro_skills_updated"] += 1
        uow.micro_skills.save(
            MicroSkillNode(
                node_id=node.node_id,
                subject_code=node.subject_code,
                grade=node.grade,
                section_code=node.section_code,
                section_name=node.section_name,
                micro_skill_name=node.micro_skill_name,
                predecessor_ids=node.predecessor_ids,
                criticality=CriticalityLevel(node.criticality),
                source_ref=node.source_ref,
            )
        )
        uow.commit()
        seen_nodes.add(node.node_id)

    for test in payload.tests:
        if uow.subjects.get(test.subject_code) is None:
            raise HTTPException(
                status_code=422,
                detail=f"Test references unknown subject_code: {test.subject_code}",
            )
        for question in test.questions:
            if uow.micro_skills.get(question.node_id) is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"Question references unknown node_id: {question.node_id}",
                )

        test_id = uuid5(
            NAMESPACE_URL,
            f"{body.source_id}:test:{test.external_id}",
        )
        existing_test = uow.tests.get(test_id)
        questions = [
            Question(
                question_id=uuid5(
                    NAMESPACE_URL,
                    (
                        f"{body.source_id}:test:{test.external_id}"
                        f":question:{question.external_id}"
                    ),
                ),
                node_id=question.node_id,
                text=question.text,
                answer_key=question.answer_key,
                max_score=question.max_score,
            )
            for question in test.questions
        ]
        if existing_test is None:
            aggregate = AssessmentTest(
                test_id=test_id,
                subject_code=test.subject_code,
                grade=test.grade,
                questions=questions,
                version=1,
            )
        else:
            aggregate = AssessmentTest(
                test_id=test_id,
                subject_code=test.subject_code,
                grade=test.grade,
                questions=questions,
                version=existing_test.version + 1,
                created_at=existing_test.created_at,
            )
        aggregate.validate()
        if existing_test is None:
            details["tests_created"] += 1
        else:
            details["tests_updated"] += 1
        uow.tests.save(aggregate)
        uow.commit()

    imported_total = sum(details.values())
    return ContentImportResponse(
        source_id=body.source_id,
        imported=imported_total,
        status="completed",
        details=details,
    )


@router.post("/tests", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
@router.post(
    "/admin/tests",
    response_model=TestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_test(body: CreateTestRequest) -> TestResponse:
    try:
        test = handle_create_test(
            CreateTestCommand(
                subject_code=body.subject_code,
                grade=body.grade,
                questions=[
                    QuestionInput(
                        node_id=q.node_id,
                        text=q.text,
                        answer_key=q.answer_key,
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
                max_score=q.max_score,
            )
            for q in test.questions
        ],
    )


@router.get("/tests", response_model=list[TestResponse])
@router.get("/admin/tests", response_model=list[TestResponse])
def list_tests() -> list[TestResponse]:
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
                    max_score=q.max_score,
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
def publish_test(test_id: UUID) -> PublishTestResponse:
    if uow.tests.get(test_id) is None:
        raise HTTPException(status_code=404, detail="test not found")
    return PublishTestResponse(test_id=test_id, status="published")


@router.post(
    "/admin/subjects",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subject(body: SubjectCreateRequest) -> SubjectResponse:
    try:
        subject = handle_create_subject(
            CreateSubjectCommand(code=body.code, name=body.name), uow=uow
        )
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return SubjectResponse(code=subject.code, name=subject.name)


@router.get("/admin/subjects", response_model=list[SubjectResponse])
def list_subjects() -> list[SubjectResponse]:
    subjects = handle_list_subjects(ListSubjectsQuery(), uow=uow)
    return [SubjectResponse(code=s.code, name=s.name) for s in subjects]


@router.post(
    "/admin/topics",
    response_model=TopicResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_topic(body: TopicCreateRequest) -> TopicResponse:
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
def list_topics() -> list[TopicResponse]:
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
def create_micro_skill(body: MicroSkillCreateRequest) -> MicroSkillResponse:
    try:
        node = handle_create_micro_skill(
            CreateMicroSkillCommand(
                node_id=body.node_id,
                subject_code=body.subject_code,
                grade=body.grade,
                section_code=body.section_code,
                section_name=body.section_name,
                micro_skill_name=body.micro_skill_name,
                predecessor_ids=body.predecessor_ids,
                criticality=body.criticality,
                source_ref=body.source_ref,
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
        grade=node.grade,
        section_code=node.section_code,
        section_name=node.section_name,
        micro_skill_name=node.micro_skill_name,
        predecessor_ids=node.predecessor_ids,
        criticality=node.criticality,
        source_ref=node.source_ref,
        blocks_count=0,
    )


@router.post(
    "/admin/micro-skills/{node_id}/links",
    response_model=MicroSkillResponse,
)
def link_micro_skill_predecessors(
    node_id: str, body: MicroSkillLinkRequest
) -> MicroSkillResponse:
    try:
        node = handle_link_micro_skill_predecessors(
            LinkMicroSkillPredecessorsCommand(
                node_id=node_id, predecessor_ids=body.predecessor_ids
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
        grade=node.grade,
        section_code=node.section_code,
        section_name=node.section_name,
        micro_skill_name=node.micro_skill_name,
        predecessor_ids=node.predecessor_ids,
        criticality=node.criticality,
        source_ref=node.source_ref,
        blocks_count=blocks_count,
    )


@router.get("/admin/micro-skills", response_model=list[MicroSkillResponse])
def list_micro_skills() -> list[MicroSkillResponse]:
    nodes = handle_list_micro_skills(ListMicroSkillsQuery(), uow=uow)
    return [
        MicroSkillResponse(
            node_id=item["node"].node_id,
            subject_code=item["node"].subject_code,
            grade=item["node"].grade,
            section_code=item["node"].section_code,
            section_name=item["node"].section_name,
            micro_skill_name=item["node"].micro_skill_name,
            predecessor_ids=item["node"].predecessor_ids,
            criticality=item["node"].criticality,
            source_ref=item["node"].source_ref,
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
def assign_test(body: AssignTestRequest) -> AssignmentResponse:
    try:
        assignment = handle_assign_test(
            AssignTestCommand(test_id=body.test_id, child_id=body.child_id), uow=uow
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return AssignmentResponse(
        assignment_id=assignment.assignment_id,
        test_id=assignment.test_id,
        child_id=assignment.child_id,
        status=assignment.status.value,
    )


@router.get(
    "/user/children/{child_id}/assignments",
    response_model=list[AssignmentListItemResponse],
)
def list_assignments_by_child(child_id: UUID) -> list[AssignmentListItemResponse]:
    assignments = uow.assignments.list_by_child(child_id)
    return [
        AssignmentListItemResponse(
            assignment_id=a.assignment_id,
            test_id=a.test_id,
            status=a.status.value,
        )
        for a in assignments
    ]


@router.post("/attempts/start", response_model=StartAttemptResponse)
def start_attempt(body: StartAttemptRequest) -> StartAttemptResponse:
    try:
        attempt = handle_start_attempt(
            StartAttemptCommand(
                assignment_id=body.assignment_id, child_id=body.child_id
            ),
            uow=uow,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return StartAttemptResponse(
        attempt_id=attempt.attempt_id,
        assignment_id=attempt.assignment_id,
        child_id=attempt.child_id,
        status=attempt.status.value,
    )


@router.post(
    "/user/assignments/{assignment_id}/start",
    response_model=StartAttemptResponse,
)
def start_attempt_for_assignment(
    assignment_id: UUID, body: StartAttemptByAssignmentRequest
) -> StartAttemptResponse:
    return start_attempt(
        StartAttemptRequest(assignment_id=assignment_id, child_id=body.child_id)
    )


@router.post(
    "/attempts/{attempt_id}/submit",
    response_model=SubmitAttemptResponse,
)
@router.post(
    "/user/attempts/{attempt_id}/submit",
    response_model=SubmitAttemptResponse,
)
def submit_attempt(
    attempt_id: UUID, body: SubmitAttemptRequest
) -> SubmitAttemptResponse:
    try:
        result = handle_submit_attempt(
            SubmitAttemptCommand(
                attempt_id=attempt_id,
                answers=[
                    SubmittedAnswerInput(question_id=a.question_id, value=a.value)
                    for a in body.answers
                ],
            ),
            uow=uow,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return SubmitAttemptResponse(**result)


@router.post(
    "/user/attempts/{attempt_id}/answers",
    response_model=SaveAttemptAnswersResponse,
)
def save_attempt_answers(
    attempt_id: UUID, body: SaveAttemptAnswersRequest
) -> SaveAttemptAnswersResponse:
    if uow.attempts.get(attempt_id) is None:
        raise HTTPException(status_code=404, detail="attempt not found")
    return SaveAttemptAnswersResponse(
        attempt_id=str(attempt_id), saved_answers=len(body.answers)
    )


@router.get("/attempts/{attempt_id}", response_model=AttemptResultResponse)
def get_attempt_result(attempt_id: UUID) -> AttemptResultResponse:
    try:
        result = handle_get_attempt_result(
            GetAttemptResultQuery(attempt_id=attempt_id), uow=uow
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AttemptResultResponse(
        attempt_id=result["attempt_id"],
        status=result["status"],
        score=result["score"],
        answers=[
            AttemptAnswerResponse(
                question_id=a["question_id"],
                value=a["value"],
                is_correct=a["is_correct"],
                awarded_score=a["awarded_score"],
            )
            for a in result["answers"]
        ],
    )


@router.get("/user/attempts/{attempt_id}/result", response_model=AttemptResultResponse)
def get_attempt_result_for_user(attempt_id: UUID) -> AttemptResultResponse:
    return get_attempt_result(attempt_id)


@router.get(
    "/admin/diagnostics/children/{child_id}",
    response_model=ChildDiagnosticsResponse,
)
def get_child_diagnostics(child_id: UUID) -> ChildDiagnosticsResponse:
    assignments_total = len(uow.assignments.list_by_child(child_id))
    attempts_total = len(uow.attempts.list_by_child(child_id))
    return ChildDiagnosticsResponse(
        child_id=child_id,
        assignments_total=assignments_total,
        attempts_total=attempts_total,
    )
