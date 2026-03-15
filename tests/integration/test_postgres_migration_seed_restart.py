from __future__ import annotations

import os
import shutil
import subprocess
import time
import uuid
from collections.abc import Generator
from importlib.util import find_spec
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from src.infrastructure.db.uow import SqlAlchemyUnitOfWork
from src.interface.http.v1.router import _import_content_with_uow
from src.interface.http.v1.schemas import ContentImportRequest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUN_INTEGRATION_TESTS = os.getenv("RUN_INTEGRATION_TESTS") == "1"
PSYCOPG_AVAILABLE = find_spec("psycopg") is not None
pytestmark = pytest.mark.skipif(
    not RUN_INTEGRATION_TESTS,
    reason="set RUN_INTEGRATION_TESTS=1 to run integration tests",
)


def _run(
    cmd: list[str], *, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.fixture()  # type: ignore[misc]
def postgres_url() -> Generator[str, None, None]:
    if shutil.which("docker") is None:
        pytest.skip("docker is not installed")

    container_name = f"assessment-it-pg-{uuid.uuid4().hex[:8]}"
    db_name = "assessment_integration"
    db_user = "monitoring"
    db_password = "asawakan"

    run_cmd = _run(
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "--name",
            container_name,
            "-e",
            f"POSTGRES_DB={db_name}",
            "-e",
            f"POSTGRES_USER={db_user}",
            "-e",
            f"POSTGRES_PASSWORD={db_password}",
            "-p",
            "0:5432",
            "postgres:16",
        ]
    )
    if run_cmd.returncode != 0:
        pytest.skip(f"cannot start postgres test container: {run_cmd.stderr.strip()}")

    try:
        port_cmd = _run(["docker", "port", container_name, "5432/tcp"])
        assert port_cmd.returncode == 0, port_cmd.stderr
        port_line = port_cmd.stdout.strip().splitlines()[0]
        host_port = int(port_line.rsplit(":", 1)[1])

        for _ in range(60):
            ready = _run(
                [
                    "docker",
                    "exec",
                    container_name,
                    "pg_isready",
                    "-U",
                    db_user,
                    "-d",
                    db_name,
                ]
            )
            if ready.returncode == 0:
                break
            time.sleep(1)
        else:
            logs = _run(["docker", "logs", container_name])
            pytest.fail(
                f"postgres test container is not ready:\n{logs.stdout}\n{logs.stderr}"
            )

        yield (
            f"postgresql+psycopg://{db_user}:{db_password}@127.0.0.1:"
            f"{host_port}/{db_name}"
        )
    finally:
        _run(["docker", "rm", "-f", container_name])


def _table_counts(database_url: str) -> dict[str, int]:
    engine = create_engine(database_url, future=True)
    with engine.connect() as conn:
        result = {
            "subjects": conn.execute(
                text("select count(*) from subjects")
            ).scalar_one(),
            "topics": conn.execute(text("select count(*) from topics")).scalar_one(),
            "micro_skill_nodes": conn.execute(
                text("select count(*) from micro_skill_nodes")
            ).scalar_one(),
        }
    engine.dispose()
    return result


def test_migration_seed_and_restart_roundtrip(postgres_url: str) -> None:
    if not PSYCOPG_AVAILABLE:
        pytest.skip("psycopg is not installed in current environment")

    env = os.environ.copy()
    env["DATABASE_URL"] = postgres_url
    env["APP_ENV"] = "test"

    upgrade = _run(["alembic", "upgrade", "head"], env=env)
    assert upgrade.returncode == 0, upgrade.stderr

    seed_first = _run(
        ["python", "-m", "scripts.seed_mvp_content", "--profile", "prod-min"],
        env=env,
    )
    assert seed_first.returncode == 0, seed_first.stderr
    counts_after_first_seed = _table_counts(postgres_url)
    assert counts_after_first_seed == {
        "subjects": 2,
        "topics": 3,
        "micro_skill_nodes": 4,
    }

    # Emulate service restart: apply migrations again and seed again.
    upgrade_second = _run(["alembic", "upgrade", "head"], env=env)
    assert upgrade_second.returncode == 0, upgrade_second.stderr

    seed_second = _run(
        ["python", "-m", "scripts.seed_mvp_content", "--profile", "prod-min"],
        env=env,
    )
    assert seed_second.returncode == 0, seed_second.stderr

    counts_after_second_seed = _table_counts(postgres_url)
    assert counts_after_second_seed == counts_after_first_seed


def test_content_import_v12_large_payload_is_idempotent_and_fast(
    postgres_url: str,
) -> None:
    if not PSYCOPG_AVAILABLE:
        pytest.skip("psycopg is not installed in current environment")

    env = os.environ.copy()
    env["DATABASE_URL"] = postgres_url
    env["APP_ENV"] = "test"

    upgrade = _run(["alembic", "upgrade", "head"], env=env)
    assert upgrade.returncode == 0, upgrade.stderr

    tests_count = 80
    questions_per_test = 5
    skill_count = 48
    subject_code = "math_v12_perf"
    topic_code = "MV12-PERF-T1"

    payload = {
        "subjects": [{"code": subject_code, "name": "Math Perf"}],
        "topics": [
            {
                "code": topic_code,
                "subject_code": subject_code,
                "grade": 2,
                "name": "Performance Topic",
            }
        ],
        "micro_skills": [
            {
                "node_id": f"MV12-PERF-N{i:03d}",
                "subject_code": subject_code,
                "topic_code": topic_code,
                "grade": 2,
                "section_code": "R1",
                "section_name": "Numbers",
                "micro_skill_name": f"Skill {i}",
                "predecessor_ids": [],
                "criticality": "medium",
                "source_ref": "integration:v1.2",
                "status": "active",
            }
            for i in range(skill_count)
        ],
        "tests": [
            {
                "external_id": f"perf-test-{i:03d}",
                "subject_code": subject_code,
                "grade": 2,
                "questions": [
                    {
                        "external_id": f"q-{i:03d}-{q:02d}",
                        "node_id": f"MV12-PERF-N{(i + q) % skill_count:03d}",
                        "text": f"{i} + {q} = ?",
                        "answer_key": str(i + q),
                        "max_score": 1,
                    }
                    for q in range(questions_per_test)
                ],
            }
            for i in range(tests_count)
        ],
    }

    request = ContentImportRequest.model_validate(
        {
            "source_id": "integration-large-v12",
            "contract_version": "v1.2",
            "payload": payload,
        }
    )

    uow_first = SqlAlchemyUnitOfWork(postgres_url)
    started_first = time.perf_counter()
    first = _import_content_with_uow(body=request, current_uow=uow_first)
    duration_first = time.perf_counter() - started_first
    uow_first.close()

    assert first.status == "completed"
    assert first.errors == []
    assert first.details is not None
    assert first.details.tests_created == tests_count
    assert first.imported > 0
    assert duration_first < 25.0

    uow_second = SqlAlchemyUnitOfWork(postgres_url)
    started_second = time.perf_counter()
    second = _import_content_with_uow(body=request, current_uow=uow_second)
    duration_second = time.perf_counter() - started_second
    uow_second.close()

    assert second.status == "completed"
    assert second.errors == []
    assert second.imported == 0
    assert second.details is not None
    assert second.details.tests_updated == 0
    assert duration_second < 20.0
