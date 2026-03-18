from __future__ import annotations

from src.application.facade import ImportContentPayloadInput
from src.interface.http.v1.schemas import ContentImportRequest


def to_import_content_payload_input(
    body: ContentImportRequest,
) -> ImportContentPayloadInput:
    return ImportContentPayloadInput(
        source_id=body.source_id,
        contract_version=body.contract_version,
        validate_only=body.validate_only,
        error_mode=body.error_mode,
        payload=body.payload.model_dump(mode="python"),
    )
