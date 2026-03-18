from __future__ import annotations

from typing import Any, Protocol

from src.application.facade import ImportContentPayloadInput
from src.interface.http.v1.schemas import (
    ContentImportDetails,
    ContentImportIssue,
    ContentImportRequest,
    ContentImportResponse,
)


class _ImportFacadeLike(Protocol):
    def import_content_payload(
        self,
        *,
        payload: ImportContentPayloadInput,
    ) -> Any: ...


def _issue_to_schema(issue: Any) -> ContentImportIssue:
    return ContentImportIssue(code=issue.code, message=issue.message, path=issue.path)


def _to_response(result: Any) -> ContentImportResponse:
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
    facade: _ImportFacadeLike,
) -> ContentImportResponse:
    result = facade.import_content_payload(
        payload=ImportContentPayloadInput(
            source_id=body.source_id,
            contract_version=body.contract_version,
            validate_only=body.validate_only,
            error_mode=body.error_mode,
            payload=body.payload.model_dump(mode="python"),
        )
    )
    return _to_response(result)
