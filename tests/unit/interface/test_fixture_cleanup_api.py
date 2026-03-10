from __future__ import annotations

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from src.infrastructure.maintenance import (
    FixtureCleanupExecution,
    FixtureCleanupFilters,
)
from src.infrastructure.maintenance.fixture_cleanup import FixtureCleanupCounts
from src.interface.http.app import create_app
from src.interface.http.v1 import router as router_module


def test_fixture_cleanup_returns_501_without_database_url() -> None:
    client = TestClient(create_app())

    response = client.post("/v1/admin/fixtures/cleanup", json={"dry_run": True})

    assert response.status_code == 501
    assert "DATABASE_URL" in response.json()["detail"]


def test_fixture_cleanup_maps_execution_result(monkeypatch: MonkeyPatch) -> None:
    def fake_run_fixture_cleanup(
        *,
        uow: object,
        dry_run: bool,
        filters: FixtureCleanupFilters,
    ) -> FixtureCleanupExecution:
        del uow
        assert dry_run is False
        assert filters.subject_code_patterns == ("^math_v\\d{2}.*$",)
        return FixtureCleanupExecution(
            dry_run=False,
            filters=FixtureCleanupFilters(
                subject_code_patterns=("^math_v\\d{2}.*$",),
                topic_code_patterns=("^MV\\d{2}.*$",),
                node_id_patterns=("^MV\\d{2}.*$",),
            ),
            matched=FixtureCleanupCounts(
                subjects=1,
                topics=2,
                micro_skills=3,
                tests=4,
                questions=5,
                assignments=6,
                attempts=7,
                answers=7,
            ),
            deleted=FixtureCleanupCounts(
                subjects=1,
                topics=2,
                micro_skills=3,
                tests=4,
                questions=5,
                assignments=6,
                attempts=7,
                answers=7,
            ),
        )

    monkeypatch.setattr(router_module, "run_fixture_cleanup", fake_run_fixture_cleanup)
    client = TestClient(create_app())
    response = client.post("/v1/admin/fixtures/cleanup", json={"dry_run": False})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["dry_run"] is False
    assert body["matched"]["micro_skills"] == 3
    assert body["deleted"]["answers"] == 7
