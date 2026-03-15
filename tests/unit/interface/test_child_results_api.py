from uuid import uuid4

from fastapi.testclient import TestClient

from src.interface.http.app import create_app


def test_child_results_returns_attempts_and_diagnostic_summary() -> None:
    client = TestClient(create_app())
    prefix = uuid4().hex[:8]
    child_id = str(uuid4())

    subject_code = f"math_{prefix}"
    topic_code = f"TOP_{prefix}"
    node_id = f"NODE_{prefix}"

    subject_res = client.post(
        "/v1/admin/subjects",
        json={"code": subject_code, "name": f"Math {prefix}"},
    )
    assert subject_res.status_code == 201

    topic_res = client.post(
        "/v1/admin/topics",
        json={
            "code": topic_code,
            "subject_code": subject_code,
            "grade": 2,
            "name": f"Topic {prefix}",
        },
    )
    assert topic_res.status_code == 201

    micro_skill_res = client.post(
        "/v1/admin/micro-skills",
        json={
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
        },
    )
    assert micro_skill_res.status_code == 201

    test_res = client.post(
        "/v1/admin/tests",
        json={
            "subject_code": subject_code,
            "grade": 2,
            "questions": [
                {
                    "node_id": node_id,
                    "text": "1 + 2 = ?",
                    "question_type": "text",
                    "answer_key": "3",
                    "text_distractors": [
                        {
                            "pattern": "2",
                            "match_mode": "exact",
                            "diagnostic_tag": "inattention",
                        }
                    ],
                    "max_score": 1,
                }
            ],
        },
    )
    assert test_res.status_code == 201
    test_payload = test_res.json()

    assign_res = client.post(
        "/v1/admin/assignments",
        json={"test_id": test_payload["test_id"], "child_id": child_id},
    )
    assert assign_res.status_code == 201
    assignment_id = assign_res.json()["assignment_id"]

    start_res = client.post(
        f"/v1/user/assignments/{assignment_id}/start",
        json={"child_id": child_id},
    )
    assert start_res.status_code == 200
    attempt_id = start_res.json()["attempt_id"]

    question_id = test_payload["questions"][0]["question_id"]
    submit_res = client.post(
        f"/v1/user/attempts/{attempt_id}/submit",
        json={
            "answers": [
                {
                    "question_id": question_id,
                    "value": "2",
                }
            ]
        },
    )
    assert submit_res.status_code == 200

    report_res = client.get(f"/v1/admin/results/children/{child_id}")
    assert report_res.status_code == 200

    report = report_res.json()
    assert report["child_id"] == child_id
    assert report["summary"]["attempts_total"] == 1
    assert report["summary"]["submitted_attempts_total"] == 1
    assert report["summary"]["started_attempts_total"] == 0
    assert report["summary"]["answers_total"] == 1
    assert report["summary"]["expected_answers_total"] == 1
    assert report["summary"]["correct_answers_total"] == 0
    assert report["summary"]["accuracy_percent"] == 0.0
    assert report["summary"]["attempts_with_diagnostics_total"] == 1
    assert report["summary"]["resolved_diagnostic_tags"] == [
        {"tag": "inattention", "count": 1}
    ]

    assert len(report["attempts"]) == 1
    row = report["attempts"][0]
    assert row["attempt_id"] == attempt_id
    assert row["assignment_id"] == assignment_id
    assert row["answers_total"] == 1
    assert row["expected_answers_total"] == 1
    assert row["unanswered_answers_total"] == 0
    assert row["correct_answers"] == 0
    assert row["accuracy_percent"] == 0.0
    assert row["has_resolved_diagnostics"] is True
    assert row["resolved_diagnostic_tags"] == [{"tag": "inattention", "count": 1}]
    assert row["started_at"]
