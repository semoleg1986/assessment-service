from __future__ import annotations

from src.application.commands.import_content import (
    ImportContentCommand,
    ImportContentIssue,
    ImportContentPayloadInput,
    ImportContentResult,
    ImportMicroSkillInput,
    ImportQuestionInput,
    ImportSubjectInput,
    ImportTestInput,
    ImportTopicInput,
)
from src.application.handlers.commands.import_content import handle_import_content
from src.application.ports.unit_of_work import UnitOfWork
from src.interface.http.v1.schemas import (
    ContentImportDetails,
    ContentImportIssue,
    ContentImportRequest,
    ContentImportResponse,
)


def _to_command(body: ContentImportRequest) -> ImportContentCommand:
    return ImportContentCommand(
        source_id=body.source_id,
        contract_version=body.contract_version,
        validate_only=body.validate_only,
        error_mode=body.error_mode,
        payload=ImportContentPayloadInput(
            subjects=[
                ImportSubjectInput(code=item.code, name=item.name)
                for item in body.payload.subjects
            ],
            topics=[
                ImportTopicInput(
                    code=item.code,
                    subject_code=item.subject_code,
                    grade=item.grade,
                    name=item.name,
                )
                for item in body.payload.topics
            ],
            micro_skills=[
                ImportMicroSkillInput(
                    node_id=item.node_id,
                    subject_code=item.subject_code,
                    topic_code=item.topic_code,
                    grade=item.grade,
                    section_code=item.section_code,
                    section_name=item.section_name,
                    micro_skill_name=item.micro_skill_name,
                    predecessor_ids=item.predecessor_ids,
                    criticality=item.criticality,
                    source_ref=item.source_ref,
                    description=item.description,
                    status=item.status,
                    external_ref=item.external_ref,
                )
                for item in body.payload.micro_skills
            ],
            tests=[
                ImportTestInput(
                    external_id=item.external_id,
                    subject_code=item.subject_code,
                    grade=item.grade,
                    questions=[
                        ImportQuestionInput(
                            external_id=question.external_id,
                            node_id=question.node_id,
                            text=question.text,
                            answer_key=question.answer_key,
                            max_score=question.max_score,
                        )
                        for question in item.questions
                    ],
                )
                for item in body.payload.tests
            ],
        ),
    )


def _issue_to_schema(issue: ImportContentIssue) -> ContentImportIssue:
    return ContentImportIssue(code=issue.code, message=issue.message, path=issue.path)


def _to_response(result: ImportContentResult) -> ContentImportResponse:
    details = None
    if result.details is not None:
        details = ContentImportDetails(
            subjects_created=result.details.subjects_created,
            subjects_updated=result.details.subjects_updated,
            topics_created=result.details.topics_created,
            topics_updated=result.details.topics_updated,
            micro_skills_created=result.details.micro_skills_created,
            micro_skills_updated=result.details.micro_skills_updated,
            tests_created=result.details.tests_created,
            tests_updated=result.details.tests_updated,
            tests_failed=result.details.tests_failed,
            questions_failed=result.details.questions_failed,
        )
    return ContentImportResponse(
        import_id=result.import_id,
        source_id=result.source_id,
        imported=result.imported,
        status=result.status,
        errors=[_issue_to_schema(item) for item in result.errors],
        warnings=[_issue_to_schema(item) for item in result.warnings],
        details=details,
    )


def import_content_with_uow(
    *,
    body: ContentImportRequest,
    current_uow: UnitOfWork,
) -> ContentImportResponse:
    result = handle_import_content(_to_command(body), uow=current_uow)
    return _to_response(result)
