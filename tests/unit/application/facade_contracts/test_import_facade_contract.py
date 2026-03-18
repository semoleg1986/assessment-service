from __future__ import annotations

from src.application.facade import AssessmentImportFacade, ImportContentPayloadInput
from src.domain.shared.statuses import CriticalityLevel, MicroSkillStatus
from src.infrastructure.uow import InMemoryUnitOfWork


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
        payload=ImportContentPayloadInput(
            source_id="facade-contract",
            contract_version="v1.2",
            validate_only=True,
            error_mode="collect",
            payload=payload,
        )
    )
    assert validated.status in {"validated", "validated_with_errors"}
    assert validated.errors == []

    applied = facade.import_content_payload(
        payload=ImportContentPayloadInput(
            source_id="facade-contract",
            contract_version="v1.2",
            validate_only=False,
            error_mode="collect",
            payload=payload,
        )
    )
    assert applied.status in {"completed", "completed_with_errors"}
    assert applied.errors == []
    assert applied.imported == 3

    idempotent = facade.import_content_payload(
        payload=ImportContentPayloadInput(
            source_id="facade-contract",
            contract_version="v1.2",
            validate_only=False,
            error_mode="collect",
            payload=payload,
        )
    )
    assert idempotent.status in {"completed", "completed_with_errors"}
    assert idempotent.errors == []
    assert idempotent.imported == 0
