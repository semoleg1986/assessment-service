from __future__ import annotations

from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid4, uuid5

from src.application.commands import (
    CreateMicroSkillCommand,
    CreateSubjectCommand,
    CreateTopicCommand,
)
from src.application.handlers import (
    handle_create_micro_skill,
    handle_create_subject,
    handle_create_topic,
)
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.aggregates.test_aggregate import AssessmentTest
from src.domain.entities.micro_skill_node import MicroSkillNode
from src.domain.entities.question import Question
from src.domain.entities.subject import Subject
from src.domain.entities.topic import Topic
from src.domain.errors import InvariantViolationError, NotFoundError
from src.domain.value_objects.statuses import CriticalityLevel, MicroSkillStatus
from src.interface.http.v1.schemas import (
    ContentImportDetails,
    ContentImportIssue,
    ContentImportRequest,
    ContentImportResponse,
)


def _details_template() -> dict[str, int]:
    return {
        "subjects_created": 0,
        "subjects_updated": 0,
        "topics_created": 0,
        "topics_updated": 0,
        "micro_skills_created": 0,
        "micro_skills_updated": 0,
        "tests_created": 0,
        "tests_updated": 0,
        "tests_failed": 0,
        "questions_failed": 0,
    }


def _imported_total(details: dict[str, int]) -> int:
    return (
        details["subjects_created"]
        + details["subjects_updated"]
        + details["topics_created"]
        + details["topics_updated"]
        + details["micro_skills_created"]
        + details["micro_skills_updated"]
        + details["tests_created"]
        + details["tests_updated"]
    )


def _details_model(details: dict[str, int]) -> ContentImportDetails:
    return ContentImportDetails(**details)


def _issue(code: str, message: str, path: str) -> ContentImportIssue:
    return ContentImportIssue(code=code, message=message, path=path)


def _check_unique(items: list[str], *, label: str) -> list[ContentImportIssue]:
    if len(items) == len(set(items)):
        return []
    return [
        _issue(
            "DUPLICATE_IDENTIFIER",
            f"Duplicate identifiers in import payload: {label}",
            label,
        )
    ]


def _detect_payload_cycles(payload: ContentImportRequest) -> list[ContentImportIssue]:
    payload_nodes = {node.node_id for node in payload.payload.micro_skills}
    graph: dict[str, list[str]] = {}
    for node in payload.payload.micro_skills:
        graph[node.node_id] = [
            pred for pred in node.predecessor_ids if pred in payload_nodes
        ]

    cycles: list[ContentImportIssue] = []
    color: dict[str, int] = {}
    stack: list[str] = []

    def dfs(node_id: str) -> None:
        color[node_id] = 1
        stack.append(node_id)
        for parent in graph.get(node_id, []):
            parent_state = color.get(parent, 0)
            if parent_state == 0:
                dfs(parent)
                continue
            if parent_state == 1:
                cycle_start = stack.index(parent)
                cycle_path = stack[cycle_start:] + [parent]
                cycles.append(
                    _issue(
                        "CYCLE_DETECTED",
                        "Cycle detected in micro-skill predecessor graph: "
                        + " -> ".join(cycle_path),
                        f"micro_skills[{node_id}].predecessor_ids",
                    )
                )
        stack.pop()
        color[node_id] = 2

    for node_id in graph:
        if color.get(node_id, 0) == 0:
            dfs(node_id)
    return cycles


def _predict_details(
    body: ContentImportRequest,
    *,
    current_uow: UnitOfWork,
    skipped_test_ids: set[str] | None = None,
) -> dict[str, int]:
    details = _details_template()
    payload = body.payload
    for subject in payload.subjects:
        existing_subject = current_uow.subjects.get(subject.code)
        if existing_subject is None:
            details["subjects_created"] += 1
        elif existing_subject.name != subject.name:
            details["subjects_updated"] += 1

    for topic in payload.topics:
        existing_topic = current_uow.topics.get(topic.code)
        if existing_topic is None:
            details["topics_created"] += 1
        elif (
            existing_topic.subject_code != topic.subject_code
            or existing_topic.grade != topic.grade
            or existing_topic.name != topic.name
        ):
            details["topics_updated"] += 1

    for node in payload.micro_skills:
        existing_node = current_uow.micro_skills.get(node.node_id)
        if existing_node is None:
            details["micro_skills_created"] += 1
        elif (
            existing_node.subject_code != node.subject_code
            or existing_node.topic_code != node.topic_code
            or existing_node.grade != node.grade
            or existing_node.section_code != node.section_code
            or existing_node.section_name != node.section_name
            or existing_node.micro_skill_name != node.micro_skill_name
            or existing_node.predecessor_ids != node.predecessor_ids
            or existing_node.criticality.value != node.criticality.value
            or existing_node.source_ref != node.source_ref
            or existing_node.description != node.description
            or existing_node.status.value != node.status.value
            or existing_node.external_ref != node.external_ref
        ):
            details["micro_skills_updated"] += 1

    for test in payload.tests:
        if skipped_test_ids and test.external_id in skipped_test_ids:
            continue
        test_id = uuid5(NAMESPACE_URL, f"{body.source_id}:test:{test.external_id}")
        existing_test = current_uow.tests.get(test_id)
        question_tuples = [
            (
                uuid5(
                    NAMESPACE_URL,
                    (
                        f"{body.source_id}:test:{test.external_id}:question:"
                        f"{question.external_id}"
                    ),
                ),
                question.node_id,
                question.text,
                question.answer_key,
                question.max_score,
            )
            for question in test.questions
        ]
        if existing_test is None:
            details["tests_created"] += 1
            continue
        existing_question_tuples = [
            (
                question.question_id,
                question.node_id,
                question.text,
                question.answer_key,
                question.max_score,
            )
            for question in sorted(
                existing_test.questions, key=lambda q: str(q.question_id)
            )
        ]
        same_test = (
            existing_test.subject_code == test.subject_code
            and existing_test.grade == test.grade
            and existing_question_tuples == question_tuples
        )
        if not same_test:
            details["tests_updated"] += 1
    return details


def _collect_test_entity_errors(
    *,
    body: ContentImportRequest,
    known_subject_codes: set[str],
    known_node_ids: set[str],
) -> dict[str, list[ContentImportIssue]]:
    payload = body.payload
    errors_by_test: dict[str, list[ContentImportIssue]] = {}
    for test in payload.tests:
        test_errors: list[ContentImportIssue] = []
        if test.subject_code not in known_subject_codes:
            test_errors.append(
                _issue(
                    "UNKNOWN_REFERENCE",
                    f"Test references unknown subject_code: {test.subject_code}",
                    f"tests[{test.external_id}].subject_code",
                )
            )
        for question in test.questions:
            if question.node_id not in known_node_ids:
                test_errors.append(
                    _issue(
                        "UNKNOWN_REFERENCE",
                        f"Question references unknown node_id: {question.node_id}",
                        (
                            f"tests[{test.external_id}].questions["
                            f"{question.external_id}].node_id"
                        ),
                    )
                )
        if test_errors:
            errors_by_test[test.external_id] = test_errors
    return errors_by_test


def _flatten_test_errors(
    errors_by_test: dict[str, list[ContentImportIssue]],
) -> list[ContentImportIssue]:
    result: list[ContentImportIssue] = []
    for issues in errors_by_test.values():
        result.extend(issues)
    return result


def _count_question_errors(issues: list[ContentImportIssue]) -> int:
    return sum(1 for issue in issues if ".questions[" in issue.path)


def import_content_with_uow(
    *, body: ContentImportRequest, current_uow: UnitOfWork
) -> ContentImportResponse:
    import_id = str(uuid4())
    payload = body.payload
    is_v12 = body.contract_version.startswith("v1.2")
    errors: list[ContentImportIssue] = []

    if not body.contract_version.startswith("v1"):
        errors.append(
            _issue(
                "UNSUPPORTED_CONTRACT_VERSION",
                "Unsupported contract_version, expected v1*",
                "contract_version",
            )
        )

    errors.extend(
        _check_unique([s.code for s in payload.subjects], label="subjects.code")
    )
    errors.extend(_check_unique([t.code for t in payload.topics], label="topics.code"))
    errors.extend(
        _check_unique(
            [m.node_id for m in payload.micro_skills], label="micro_skills.node_id"
        )
    )
    errors.extend(
        _check_unique([t.external_id for t in payload.tests], label="tests.external_id")
    )
    for test in payload.tests:
        errors.extend(
            _check_unique(
                [q.external_id for q in test.questions],
                label=f"tests[{test.external_id}].questions.external_id",
            )
        )

    existing_subject_codes = {subject.code for subject in current_uow.subjects.list()}
    payload_subject_codes = {subject.code for subject in payload.subjects}
    known_subject_codes = existing_subject_codes | payload_subject_codes
    existing_topics = {topic.code: topic for topic in current_uow.topics.list()}
    payload_topics = {topic.code: topic for topic in payload.topics}
    known_topic_codes = set(existing_topics) | set(payload_topics)

    existing_node_ids = {node.node_id for node in current_uow.micro_skills.list()}
    payload_node_ids = {node.node_id for node in payload.micro_skills}
    known_node_ids = existing_node_ids | payload_node_ids

    for topic in payload.topics:
        if topic.subject_code not in known_subject_codes:
            errors.append(
                _issue(
                    "UNKNOWN_REFERENCE",
                    f"Topic references unknown subject_code: {topic.subject_code}",
                    f"topics[{topic.code}].subject_code",
                )
            )

    for node in payload.micro_skills:
        if node.subject_code not in known_subject_codes:
            errors.append(
                _issue(
                    "UNKNOWN_REFERENCE",
                    f"Micro-skill references unknown subject_code: {node.subject_code}",
                    f"micro_skills[{node.node_id}].subject_code",
                )
            )
        if node.topic_code not in known_topic_codes:
            errors.append(
                _issue(
                    "UNKNOWN_REFERENCE",
                    f"Micro-skill references unknown topic_code: {node.topic_code}",
                    f"micro_skills[{node.node_id}].topic_code",
                )
            )
        resolved_topic = payload_topics.get(node.topic_code) or existing_topics.get(
            node.topic_code
        )
        if resolved_topic and (
            resolved_topic.subject_code != node.subject_code
            or resolved_topic.grade != node.grade
        ):
            errors.append(
                _issue(
                    "TOPIC_MISMATCH",
                    (
                        "Topic must match micro-skill subject_code and grade: "
                        f"{node.topic_code}"
                    ),
                    f"micro_skills[{node.node_id}].topic_code",
                )
            )
        for pred in node.predecessor_ids:
            if pred not in known_node_ids:
                errors.append(
                    _issue(
                        "UNKNOWN_REFERENCE",
                        f"Unknown predecessor_id: {pred} for node {node.node_id}",
                        f"micro_skills[{node.node_id}].predecessor_ids",
                    )
                )

    errors.extend(_detect_payload_cycles(body))

    test_errors_by_entity = _collect_test_entity_errors(
        body=body,
        known_subject_codes=known_subject_codes,
        known_node_ids=known_node_ids,
    )
    test_errors = _flatten_test_errors(test_errors_by_entity)

    if not is_v12:
        errors.extend(test_errors)

    if errors:
        if body.error_mode == "fail_fast":
            errors = [errors[0]]
        return ContentImportResponse(
            import_id=import_id,
            source_id=body.source_id,
            imported=0,
            status="failed",
            errors=errors,
            warnings=[],
            details=_details_model(_details_template()),
        )

    if body.validate_only:
        predicted = _predict_details(
            body,
            current_uow=current_uow,
            skipped_test_ids=set(test_errors_by_entity) if is_v12 else None,
        )
        status_value = "validated"
        validation_errors: list[ContentImportIssue] = []
        if is_v12 and test_errors:
            predicted["tests_failed"] = len(test_errors_by_entity)
            predicted["questions_failed"] = _count_question_errors(test_errors)
            status_value = "validated_with_errors"
            validation_errors = test_errors
            if body.error_mode == "fail_fast":
                validation_errors = validation_errors[:1]
        return ContentImportResponse(
            import_id=import_id,
            source_id=body.source_id,
            imported=_imported_total(predicted),
            status=status_value,
            errors=validation_errors,
            warnings=[],
            details=_details_model(predicted),
        )

    details = _details_template()

    for subject in payload.subjects:
        existing_subject = current_uow.subjects.get(subject.code)
        if existing_subject is None:
            details["subjects_created"] += 1
            handle_create_subject(
                CreateSubjectCommand(code=subject.code, name=subject.name),
                uow=current_uow,
            )
            continue

        elif existing_subject.name != subject.name:
            details["subjects_updated"] += 1
        current_uow.subjects.save(
            Subject(
                code=subject.code,
                name=subject.name,
            )
        )
        current_uow.commit()

    for topic in payload.topics:
        existing_topic = current_uow.topics.get(topic.code)
        if existing_topic is None:
            details["topics_created"] += 1
            handle_create_topic(
                CreateTopicCommand(
                    code=topic.code,
                    subject_code=topic.subject_code,
                    grade=topic.grade,
                    name=topic.name,
                ),
                uow=current_uow,
            )
            continue
        changed = (
            existing_topic.subject_code != topic.subject_code
            or existing_topic.grade != topic.grade
            or existing_topic.name != topic.name
        )
        if changed:
            details["topics_updated"] += 1
        current_uow.topics.save(
            Topic(
                code=topic.code,
                subject_code=topic.subject_code,
                grade=topic.grade,
                name=topic.name,
            )
        )
        current_uow.commit()

    for node in payload.micro_skills:
        existing_node = current_uow.micro_skills.get(node.node_id)
        if existing_node is None:
            details["micro_skills_created"] += 1
            handle_create_micro_skill(
                CreateMicroSkillCommand(
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
                ),
                uow=current_uow,
            )
            continue

        changed = (
            existing_node.subject_code != node.subject_code
            or existing_node.topic_code != node.topic_code
            or existing_node.grade != node.grade
            or existing_node.section_code != node.section_code
            or existing_node.section_name != node.section_name
            or existing_node.micro_skill_name != node.micro_skill_name
            or existing_node.predecessor_ids != node.predecessor_ids
            or existing_node.criticality.value != node.criticality.value
            or existing_node.source_ref != node.source_ref
            or existing_node.description != node.description
            or existing_node.status.value != node.status.value
            or existing_node.external_ref != node.external_ref
        )
        if changed:
            details["micro_skills_updated"] += 1
        updated_at = existing_node.updated_at
        version = existing_node.version
        if changed:
            version += 1
            updated_at = datetime.now(UTC)
        current_uow.micro_skills.save(
            MicroSkillNode(
                node_id=node.node_id,
                subject_code=node.subject_code,
                topic_code=node.topic_code,
                grade=node.grade,
                section_code=node.section_code,
                section_name=node.section_name,
                micro_skill_name=node.micro_skill_name,
                predecessor_ids=node.predecessor_ids,
                criticality=CriticalityLevel(node.criticality),
                source_ref=node.source_ref,
                description=node.description,
                status=MicroSkillStatus(node.status),
                external_ref=node.external_ref,
                version=version,
                created_at=existing_node.created_at,
                updated_at=updated_at,
            )
        )
        if changed:
            current_uow.commit()

    apply_errors: list[ContentImportIssue] = []
    for test in payload.tests:
        test_entity_errors = test_errors_by_entity.get(test.external_id, [])
        if is_v12 and test_entity_errors:
            details["tests_failed"] += 1
            details["questions_failed"] += _count_question_errors(test_entity_errors)
            apply_errors.extend(test_entity_errors)
            continue

        test_id = uuid5(
            NAMESPACE_URL,
            f"{body.source_id}:test:{test.external_id}",
        )
        existing_test = current_uow.tests.get(test_id)
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
        should_save = True
        try:
            if existing_test is None:
                aggregate = AssessmentTest(
                    test_id=test_id,
                    subject_code=test.subject_code,
                    grade=test.grade,
                    questions=questions,
                    version=1,
                )
            else:
                existing_question_tuples = [
                    (
                        question.question_id,
                        question.node_id,
                        question.text,
                        question.answer_key,
                        question.max_score,
                    )
                    for question in sorted(
                        existing_test.questions, key=lambda q: str(q.question_id)
                    )
                ]
                incoming_question_tuples = [
                    (
                        question.question_id,
                        question.node_id,
                        question.text,
                        question.answer_key,
                        question.max_score,
                    )
                    for question in questions
                ]
                same_test = (
                    existing_test.subject_code == test.subject_code
                    and existing_test.grade == test.grade
                    and existing_question_tuples == incoming_question_tuples
                )
                if same_test:
                    should_save = False
                    aggregate = existing_test
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
            elif should_save:
                details["tests_updated"] += 1
            if should_save:
                current_uow.tests.save(aggregate)
                current_uow.commit()
        except (InvariantViolationError, NotFoundError) as exc:
            if not is_v12:
                raise
            details["tests_failed"] += 1
            details["questions_failed"] += len(test.questions)
            apply_errors.append(
                _issue(
                    "ENTITY_VALIDATION_FAILED",
                    str(exc),
                    f"tests[{test.external_id}]",
                )
            )

    imported_total = _imported_total(details)
    status_value = "completed"
    response_errors: list[ContentImportIssue] = []
    if is_v12 and apply_errors:
        status_value = "completed_with_errors"
        response_errors = apply_errors
        if body.error_mode == "fail_fast":
            response_errors = response_errors[:1]

    return ContentImportResponse(
        import_id=import_id,
        source_id=body.source_id,
        imported=imported_total,
        status=status_value,
        errors=response_errors,
        warnings=[],
        details=_details_model(details),
    )
