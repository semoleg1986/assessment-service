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


def test_child_skill_results_returns_gap_levels_and_recommendations() -> None:
    client = TestClient(create_app())
    prefix = uuid4().hex[:8]
    child_id = str(uuid4())

    subject_code = f"math_{prefix}"
    topic_code = f"TOP_{prefix}"
    primary_node_id = f"NODE_A_{prefix}"
    secondary_node_id = f"NODE_B_{prefix}"

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

    for node_id, skill_name in [
        (primary_node_id, f"Primary {prefix}"),
        (secondary_node_id, f"Secondary {prefix}"),
    ]:
        micro_skill_res = client.post(
            "/v1/admin/micro-skills",
            json={
                "node_id": node_id,
                "subject_code": subject_code,
                "topic_code": topic_code,
                "grade": 2,
                "section_code": "R1",
                "section_name": "Numbers",
                "micro_skill_name": skill_name,
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
                    "node_id": primary_node_id,
                    "text": "2 + 2 = ?",
                    "question_type": "text",
                    "answer_key": "4",
                    "text_distractors": [
                        {
                            "pattern": "5",
                            "match_mode": "exact",
                            "diagnostic_tag": "calc_error",
                        }
                    ],
                    "max_score": 1,
                },
                {
                    "node_id": primary_node_id,
                    "text": "3 + 1 = ?",
                    "question_type": "text",
                    "answer_key": "4",
                    "text_distractors": [
                        {
                            "pattern": "3",
                            "match_mode": "exact",
                            "diagnostic_tag": "inattention",
                        }
                    ],
                    "max_score": 1,
                },
                {
                    "node_id": primary_node_id,
                    "text": "6 - 2 = ?",
                    "question_type": "text",
                    "answer_key": "4",
                    "text_distractors": [
                        {
                            "pattern": "2",
                            "match_mode": "exact",
                            "diagnostic_tag": "concept_gap",
                        }
                    ],
                    "max_score": 1,
                },
                {
                    "node_id": secondary_node_id,
                    "text": "5 + 0 = ?",
                    "question_type": "text",
                    "answer_key": "5",
                    "max_score": 1,
                },
                {
                    "node_id": secondary_node_id,
                    "text": "1 + 1 = ?",
                    "question_type": "text",
                    "answer_key": "2",
                    "max_score": 1,
                },
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

    question_ids = [question["question_id"] for question in test_payload["questions"]]
    submit_res = client.post(
        f"/v1/user/attempts/{attempt_id}/submit",
        json={
            "answers": [
                {
                    "question_id": question_ids[0],
                    "value": "5",
                    "time_spent_ms": 15000,
                },
                {
                    "question_id": question_ids[1],
                    "value": "3",
                    "time_spent_ms": 18000,
                },
                {
                    "question_id": question_ids[2],
                    "value": "2",
                    "time_spent_ms": 19000,
                },
                {
                    "question_id": question_ids[3],
                    "value": "5",
                    "time_spent_ms": 9000,
                },
                {
                    "question_id": question_ids[4],
                    "value": "2",
                    "time_spent_ms": 10000,
                },
            ]
        },
    )
    assert submit_res.status_code == 200

    report_res = client.get(f"/v1/admin/results/children/{child_id}/skills")
    assert report_res.status_code == 200
    report = report_res.json()

    assert report["child_id"] == child_id
    assert report["summary"]["total_skills"] == 2
    assert report["summary"]["high_gap_total"] == 1
    assert report["summary"]["medium_gap_total"] == 0
    assert report["summary"]["low_gap_total"] == 0
    assert report["summary"]["insufficient_data_total"] == 1
    assert report["summary"]["critical_gap_total"] == 1
    assert report["summary"]["gap_total"] == 0
    assert report["summary"]["risk_total"] == 1
    assert report["summary"]["normal_total"] == 0

    assert len(report["skills"]) == 2
    primary = report["skills"][0]
    secondary = report["skills"][1]

    assert primary["node_id"] == primary_node_id
    assert primary["attempted_questions"] == 3
    assert primary["correct_answers"] == 0
    assert primary["accuracy_percent"] == 0.0
    assert primary["gap_level"] == "high"
    assert primary["signal"] == "critical_gap"
    assert primary["wilson_low"] >= 0.0
    assert primary["wilson_high"] <= 1.0
    assert primary["recommendation"]
    assert {item["tag"] for item in primary["resolved_diagnostic_tags"]} == {
        "calc_error",
        "inattention",
        "concept_gap",
    }

    assert secondary["node_id"] == secondary_node_id
    assert secondary["attempted_questions"] == 2
    assert secondary["correct_answers"] == 2
    assert secondary["accuracy_percent"] == 100.0
    assert secondary["gap_level"] == "insufficient_data"
    assert secondary["signal"] == "risk"

    plan_res = client.get(f"/v1/admin/results/children/{child_id}/correction-plan")
    assert plan_res.status_code == 200
    plan = plan_res.json()

    assert plan["child_id"] == child_id
    assert plan["summary"]["actions_total"] == 2
    assert plan["summary"]["p1_total"] == 1
    assert plan["summary"]["p2_total"] == 0
    assert plan["summary"]["p3_total"] == 1
    assert plan["summary"]["p4_total"] == 0

    assert len(plan["actions"]) == 2
    first_action = plan["actions"][0]
    second_action = plan["actions"][1]
    assert first_action["node_id"] == primary_node_id
    assert first_action["signal"] == "critical_gap"
    assert first_action["priority"] == "P1"
    assert first_action["recommendation"]
    assert first_action["target_outcome"]
    assert second_action["node_id"] == secondary_node_id
    assert second_action["signal"] == "risk"
    assert second_action["priority"] == "P3"
