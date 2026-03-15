from __future__ import annotations

from uuid import NAMESPACE_URL, uuid4, uuid5

from src.application.content.commands.create_micro_skill import CreateMicroSkillCommand
from src.application.content.commands.create_subject import CreateSubjectCommand
from src.application.content.commands.create_topic import CreateTopicCommand
from src.application.content.commands.import_content import (
    ImportContentCommand,
    ImportContentDetails,
    ImportContentIssue,
    ImportContentResult,
    ImportQuestionOptionInput,
    ImportTextDistractorInput,
)
from src.application.content.handlers.create_micro_skill import (
    handle_create_micro_skill,
)
from src.application.content.handlers.create_subject import handle_create_subject
from src.application.content.handlers.create_topic import handle_create_topic
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.content.subject.entity import Subject
from src.domain.content.test.aggregate import AssessmentTest
from src.domain.content.test.entities.question import Question
from src.domain.content.test.entities.question_option import QuestionOption
from src.domain.content.test.entities.text_distractor import TextDistractor
from src.domain.content.topic.entity import Topic
from src.domain.errors import InvariantViolationError, NotFoundError
from src.domain.shared.questions import QuestionType


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


def _details_model(details: dict[str, int]) -> ImportContentDetails:
    return ImportContentDetails(**details)


def _issue(code: str, message: str, path: str) -> ImportContentIssue:
    return ImportContentIssue(code=code, message=message, path=path)


def _check_unique(items: list[str], *, label: str) -> list[ImportContentIssue]:
    if len(items) == len(set(items)):
        return []
    return [
        _issue(
            "DUPLICATE_IDENTIFIER",
            f"Duplicate identifiers in import payload: {label}",
            label,
        )
    ]


def _detect_payload_cycles(command: ImportContentCommand) -> list[ImportContentIssue]:
    payload_nodes = {node.node_id for node in command.payload.micro_skills}
    graph: dict[str, list[str]] = {}
    for node in command.payload.micro_skills:
        graph[node.node_id] = [
            pred for pred in node.predecessor_ids if pred in payload_nodes
        ]

    cycles: list[ImportContentIssue] = []
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


def _options_tuple(
    options: list[QuestionOption],
) -> tuple[tuple[str, str, int, str | None], ...]:
    return tuple(
        sorted(
            (
                (
                    option.option_id,
                    option.text,
                    option.position,
                    (
                        option.diagnostic_tag.value
                        if option.diagnostic_tag is not None
                        else None
                    ),
                )
                for option in options
            ),
            key=lambda item: item[2],
        )
    )


def _text_distractors_tuple(
    distractors: list[TextDistractor],
) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (
            distractor.pattern,
            distractor.match_mode.value,
            distractor.diagnostic_tag.value,
        )
        for distractor in distractors
    )


def _entity_question_tuple(question: Question) -> tuple[object, ...]:
    return (
        question.question_id,
        question.node_id,
        question.text,
        question.question_type.value,
        question.answer_key,
        question.correct_option_id,
        _options_tuple(question.options),
        _text_distractors_tuple(question.text_distractors),
        question.max_score,
    )


def _build_question_entity(
    *,
    source_id: str,
    test_external_id: str,
    question_external_id: str,
    node_id: str,
    text: str,
    question_type: QuestionType,
    answer_key: str | None,
    correct_option_id: str | None,
    max_score: int,
    options: list[ImportQuestionOptionInput],
    text_distractors: list[ImportTextDistractorInput],
) -> Question:
    return Question(
        question_id=uuid5(
            NAMESPACE_URL,
            (
                f"{source_id}:test:{test_external_id}:question:"
                f"{question_external_id}"
            ),
        ),
        node_id=node_id,
        text=text,
        question_type=question_type,
        answer_key=answer_key,
        correct_option_id=correct_option_id,
        options=[
            QuestionOption(
                option_id=option.option_id,
                text=option.text,
                position=option.position,
                diagnostic_tag=option.diagnostic_tag,
            )
            for option in options
        ],
        text_distractors=[
            TextDistractor(
                pattern=distractor.pattern,
                match_mode=distractor.match_mode,
                diagnostic_tag=distractor.diagnostic_tag,
            )
            for distractor in text_distractors
        ],
        max_score=max_score,
    )


def _predict_details(
    command: ImportContentCommand,
    *,
    current_uow: UnitOfWork,
    skipped_test_ids: set[str] | None = None,
) -> dict[str, int]:
    details = _details_template()
    payload = command.payload
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
        test_id = uuid5(NAMESPACE_URL, f"{command.source_id}:test:{test.external_id}")
        existing_test = current_uow.tests.get(test_id)
        question_tuples = [
            _entity_question_tuple(
                _build_question_entity(
                    source_id=command.source_id,
                    test_external_id=test.external_id,
                    question_external_id=question.external_id,
                    node_id=question.node_id,
                    text=question.text,
                    question_type=question.question_type,
                    answer_key=question.answer_key,
                    correct_option_id=question.correct_option_id,
                    max_score=question.max_score,
                    options=question.options,
                    text_distractors=question.text_distractors,
                )
            )
            for question in test.questions
        ]
        if existing_test is None:
            details["tests_created"] += 1
            continue
        existing_question_tuples = [
            _entity_question_tuple(question)
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
    command: ImportContentCommand,
    known_subject_codes: set[str],
    known_node_ids: set[str],
) -> dict[str, list[ImportContentIssue]]:
    payload = command.payload
    errors_by_test: dict[str, list[ImportContentIssue]] = {}
    for test in payload.tests:
        test_errors: list[ImportContentIssue] = []
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
                continue
            try:
                _build_question_entity(
                    source_id=command.source_id,
                    test_external_id=test.external_id,
                    question_external_id=question.external_id,
                    node_id=question.node_id,
                    text=question.text,
                    question_type=question.question_type,
                    answer_key=question.answer_key,
                    correct_option_id=question.correct_option_id,
                    max_score=question.max_score,
                    options=question.options,
                    text_distractors=question.text_distractors,
                ).validate()
            except InvariantViolationError as exc:
                test_errors.append(
                    _issue(
                        "ENTITY_VALIDATION_FAILED",
                        str(exc),
                        (
                            f"tests[{test.external_id}].questions["
                            f"{question.external_id}]"
                        ),
                    )
                )
        if test_errors:
            errors_by_test[test.external_id] = test_errors
    return errors_by_test


def _flatten_test_errors(
    errors_by_test: dict[str, list[ImportContentIssue]],
) -> list[ImportContentIssue]:
    result: list[ImportContentIssue] = []
    for issues in errors_by_test.values():
        result.extend(issues)
    return result


def _count_question_errors(issues: list[ImportContentIssue]) -> int:
    return sum(1 for issue in issues if ".questions[" in issue.path)


def handle_import_content(
    command: ImportContentCommand,
    *,
    uow: UnitOfWork,
) -> ImportContentResult:
    import_id = str(uuid4())
    payload = command.payload
    has_entity_level_isolation = command.contract_version.startswith(("v1.2", "v1.3"))
    errors: list[ImportContentIssue] = []

    if not command.contract_version.startswith("v1"):
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

    existing_subject_codes = {subject.code for subject in uow.subjects.list()}
    payload_subject_codes = {subject.code for subject in payload.subjects}
    known_subject_codes = existing_subject_codes | payload_subject_codes
    existing_topics = {topic.code: topic for topic in uow.topics.list()}
    payload_topics = {topic.code: topic for topic in payload.topics}
    known_topic_codes = set(existing_topics) | set(payload_topics)

    existing_node_ids = {node.node_id for node in uow.micro_skills.list()}
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

    errors.extend(_detect_payload_cycles(command))

    test_errors_by_entity = _collect_test_entity_errors(
        command=command,
        known_subject_codes=known_subject_codes,
        known_node_ids=known_node_ids,
    )
    test_errors = _flatten_test_errors(test_errors_by_entity)

    if not has_entity_level_isolation:
        errors.extend(test_errors)

    if errors:
        if command.error_mode == "fail_fast":
            errors = [errors[0]]
        return ImportContentResult(
            import_id=import_id,
            source_id=command.source_id,
            imported=0,
            status="failed",
            errors=errors,
            warnings=[],
            details=_details_model(_details_template()),
        )

    if command.validate_only:
        predicted = _predict_details(
            command,
            current_uow=uow,
            skipped_test_ids=(
                set(test_errors_by_entity) if has_entity_level_isolation else None
            ),
        )
        status_value = "validated"
        validation_errors: list[ImportContentIssue] = []
        if has_entity_level_isolation and test_errors:
            predicted["tests_failed"] = len(test_errors_by_entity)
            predicted["questions_failed"] = _count_question_errors(test_errors)
            status_value = "validated_with_errors"
            validation_errors = test_errors
            if command.error_mode == "fail_fast":
                validation_errors = validation_errors[:1]
        return ImportContentResult(
            import_id=import_id,
            source_id=command.source_id,
            imported=_imported_total(predicted),
            status=status_value,
            errors=validation_errors,
            warnings=[],
            details=_details_model(predicted),
        )

    details = _details_template()

    for subject in payload.subjects:
        existing_subject = uow.subjects.get(subject.code)
        if existing_subject is None:
            details["subjects_created"] += 1
            handle_create_subject(
                CreateSubjectCommand(code=subject.code, name=subject.name),
                uow=uow,
            )
            continue

        if existing_subject.name != subject.name:
            details["subjects_updated"] += 1
        uow.subjects.save(Subject(code=subject.code, name=subject.name))
        uow.commit()

    for topic in payload.topics:
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

    for node in payload.micro_skills:
        existing_node = uow.micro_skills.get(node.node_id)
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
                uow=uow,
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
        existing_node.update_details(
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
        )
        uow.micro_skills.save(existing_node)
        if changed:
            uow.commit()

    apply_errors: list[ImportContentIssue] = []
    for test in payload.tests:
        test_entity_errors = test_errors_by_entity.get(test.external_id, [])
        if has_entity_level_isolation and test_entity_errors:
            details["tests_failed"] += 1
            details["questions_failed"] += _count_question_errors(test_entity_errors)
            apply_errors.extend(test_entity_errors)
            continue

        test_id = uuid5(NAMESPACE_URL, f"{command.source_id}:test:{test.external_id}")
        existing_test = uow.tests.get(test_id)
        questions = [
            _build_question_entity(
                source_id=command.source_id,
                test_external_id=test.external_id,
                question_external_id=question.external_id,
                node_id=question.node_id,
                text=question.text,
                question_type=question.question_type,
                answer_key=question.answer_key,
                correct_option_id=question.correct_option_id,
                max_score=question.max_score,
                options=question.options,
                text_distractors=question.text_distractors,
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
                    _entity_question_tuple(question)
                    for question in sorted(
                        existing_test.questions,
                        key=lambda q: str(q.question_id),
                    )
                ]
                incoming_question_tuples = [
                    _entity_question_tuple(question) for question in questions
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
                    existing_test.revise(
                        subject_code=test.subject_code,
                        grade=test.grade,
                        questions=questions,
                    )
                    aggregate = existing_test
            aggregate.validate()
            if existing_test is None:
                details["tests_created"] += 1
            elif should_save:
                details["tests_updated"] += 1
            if should_save:
                uow.tests.save(aggregate)
                uow.commit()
        except (InvariantViolationError, NotFoundError) as exc:
            if not has_entity_level_isolation:
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
    response_errors: list[ImportContentIssue] = []
    if has_entity_level_isolation and apply_errors:
        status_value = "completed_with_errors"
        response_errors = apply_errors
        if command.error_mode == "fail_fast":
            response_errors = response_errors[:1]

    return ImportContentResult(
        import_id=import_id,
        source_id=command.source_id,
        imported=imported_total,
        status=status_value,
        errors=response_errors,
        warnings=[],
        details=_details_model(details),
    )
