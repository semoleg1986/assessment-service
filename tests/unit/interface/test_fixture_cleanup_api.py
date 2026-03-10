from __future__ import annotations

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from src.application.ports.fixture_cleanup import (
    FixtureCleanupCounts,
    FixtureCleanupExecution,
    FixtureCleanupFilters,
    FixtureCleanupService,
)
from src.application.ports.unit_of_work import UnitOfWork
from src.interface.http import dependencies as deps_module
from src.interface.http.app import create_app


def test_fixture_cleanup_returns_501_without_database_url() -> None:
    client = TestClient(create_app())

    response = client.post("/v1/admin/fixtures/cleanup", json={"dry_run": True})

    assert response.status_code == 501
    assert "DATABASE_URL" in response.json()["detail"]


def test_fixture_cleanup_maps_execution_result(monkeypatch: MonkeyPatch) -> None:
    class FakeCleanupService(FixtureCleanupService):
        def run(
            self,
            *,
            uow: UnitOfWork,
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

    monkeypatch.setattr(
        deps_module,
        "get_fixture_cleanup_service",
        lambda: FakeCleanupService(),
    )
    client = TestClient(create_app())
    response = client.post("/v1/admin/fixtures/cleanup", json={"dry_run": False})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["dry_run"] is False
    assert body["matched"]["micro_skills"] == 3
    assert body["deleted"]["answers"] == 7
