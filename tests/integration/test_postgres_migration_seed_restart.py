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
