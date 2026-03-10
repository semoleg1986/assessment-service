from __future__ import annotations

from typing import Any, cast
from uuid import uuid4

from fastapi.testclient import TestClient

from src.interface.http.app import create_app


def _payload(prefix: str) -> dict[str, Any]:
    subject_code = f"math_{prefix}"
    topic_code = f"T_{prefix}"
    node_id = f"N_{prefix}"
    return {
        "subjects": [{"code": subject_code, "name": f"Math {prefix}"}],
        "topics": [
            {
                "code": topic_code,
                "subject_code": subject_code,
                "grade": 2,
                "name": f"Topic {prefix}",
            }
        ],
        "micro_skills": [
            {
                "node_id": node_id,
                "subject_code": subject_code,
                "topic_code": topic_code,
                "grade": 2,
                "section_code": "R1",
                "section_name": "Numbers",
                "micro_skill_name": f"Skill {prefix}",
                "predecessor_ids": [],
                "criticality": "medium",
                "source_ref": "test",
                "description": f"Description {prefix}",
                "status": "active",
                "external_ref": f"external-{prefix}",
            }
        ],
        "tests": [
            {
                "external_id": f"test_{prefix}",
                "subject_code": subject_code,
                "grade": 2,
                "questions": [
                    {
                        "external_id": f"q_{prefix}",
                        "node_id": node_id,
                        "text": "2 + 2 = ?",
                        "answer_key": "4",
                        "max_score": 1,
                    }
                ],
            }
        ],
    }


def test_import_validate_detects_cycle() -> None:
    client = TestClient(create_app())
    prefix = uuid4().hex[:8]
    subject_code = f"math_{prefix}"
    payload = {
        "subjects": [{"code": subject_code, "name": "Math"}],
        "topics": [
            {
                "code": f"T_{prefix}",
                "subject_code": subject_code,
                "grade": 2,
                "name": f"Topic {prefix}",
            }
        ],
        "micro_skills": [
            {
                "node_id": f"A_{prefix}",
                "subject_code": subject_code,
                "topic_code": f"T_{prefix}",
                "grade": 2,
                "section_code": "R1",
                "section_name": "Numbers",
                "micro_skill_name": "A",
                "predecessor_ids": [f"B_{prefix}"],
                "criticality": "medium",
                "source_ref": "test",
            },
            {
                "node_id": f"B_{prefix}",
                "subject_code": subject_code,
                "topic_code": f"T_{prefix}",
                "grade": 2,
                "section_code": "R1",
                "section_name": "Numbers",
                "micro_skill_name": "B",
                "predecessor_ids": [f"A_{prefix}"],
                "criticality": "medium",
                "source_ref": "test",
            },
        ],
        "tests": [],
    }

    response = client.post(
        "/v1/admin/content/import",
        json={
            "source_id": f"test-{prefix}",
            "contract_version": "v1.0",
            "validate_only": True,
            "payload": payload,
        },
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "failed"
    assert any(err["code"] == "CYCLE_DETECTED" for err in body["errors"])


def test_import_validate_only_does_not_persist_data() -> None:
    client = TestClient(create_app())
    prefix = uuid4().hex[:8]
    payload = _payload(prefix)

    response = client.post(
        "/v1/admin/content/import",
        json={
            "source_id": f"test-{prefix}",
            "contract_version": "v1.0",
            "validate_only": True,
            "payload": payload,
        },
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "validated"
    assert body["errors"] == []
    assert body["imported"] > 0

    subjects = client.get("/v1/admin/subjects").json()
    assert not any(subject["code"] == f"math_{prefix}" for subject in subjects)


def test_import_apply_is_idempotent() -> None:
    client = TestClient(create_app())
    prefix = uuid4().hex[:8]
    payload = _payload(prefix)
    request_body = {
        "source_id": f"test-{prefix}",
        "contract_version": "v1.0",
        "payload": payload,
    }

    first = client.post("/v1/admin/content/import", json=request_body)
    assert first.status_code == 202
    first_body = first.json()
    assert first_body["status"] == "completed"
    assert first_body["errors"] == []
    assert first_body["imported"] > 0

    second = client.post("/v1/admin/content/import", json=request_body)
    assert second.status_code == 202
    second_body = second.json()
    assert second_body["status"] == "completed"
    assert second_body["errors"] == []
    assert second_body["imported"] == 0


def test_import_updates_micro_skill_metadata_and_version() -> None:
    client = TestClient(create_app())
    prefix = uuid4().hex[:8]
    payload = _payload(prefix)
    request_body = {
        "source_id": f"test-{prefix}",
        "contract_version": "v1.1",
        "payload": payload,
    }

    created = client.post("/v1/admin/content/import", json=request_body)
    assert created.status_code == 202
    assert created.json()["status"] == "completed"

    micro_skills = cast(list[dict[str, Any]], payload["micro_skills"])
    micro_skills[0]["description"] = "Updated description"
    micro_skills[0]["status"] = "draft"
    micro_skills[0]["external_ref"] = f"updated-{prefix}"
    updated = client.post("/v1/admin/content/import", json=request_body)
    assert updated.status_code == 202
    body = updated.json()
    assert body["status"] == "completed"
    assert body["details"]["micro_skills_updated"] == 1

    micro_skills = client.get("/v1/admin/micro-skills").json()
    target = next(item for item in micro_skills if item["node_id"] == f"N_{prefix}")
    assert target["description"] == "Updated description"
    assert target["status"] == "draft"
    assert target["external_ref"] == f"updated-{prefix}"
    assert target["version"] == 2
    assert target["created_at"]
    assert target["updated_at"]


def test_import_validate_fails_for_unknown_topic_reference() -> None:
    client = TestClient(create_app())
    prefix = uuid4().hex[:8]
    payload = _payload(prefix)
    micro_skills = cast(list[dict[str, Any]], payload["micro_skills"])
    micro_skills[0]["topic_code"] = "UNKNOWN-TOPIC"

    response = client.post(
        "/v1/admin/content/import",
        json={
            "source_id": f"test-{prefix}",
            "contract_version": "v1.1",
            "validate_only": True,
            "payload": payload,
        },
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "failed"
    assert any(err["path"].endswith(".topic_code") for err in body["errors"])
