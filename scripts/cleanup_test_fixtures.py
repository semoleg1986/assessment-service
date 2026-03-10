from __future__ import annotations

import argparse
import json
import logging

from src.infrastructure.maintenance import (
    DEFAULT_NODE_ID_PATTERNS,
    DEFAULT_SUBJECT_CODE_PATTERNS,
    DEFAULT_TOPIC_CODE_PATTERNS,
    FixtureCleanupFilters,
    run_fixture_cleanup,
)
from src.infrastructure.uow import AppSettings, build_uow

logger = logging.getLogger("assessment.cleanup")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cleanup assessment test fixtures (math_v0xx*, MV0xx*)"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply delete operations. By default script runs in dry-run mode.",
    )
    parser.add_argument(
        "--subject-pattern",
        action="append",
        dest="subject_patterns",
        help=(
            "Regex for subjects.code. Can be repeated. "
            f"Default: {', '.join(DEFAULT_SUBJECT_CODE_PATTERNS)}"
        ),
    )
    parser.add_argument(
        "--topic-pattern",
        action="append",
        dest="topic_patterns",
        help=(
            "Regex for topics.code. Can be repeated. "
            f"Default: {', '.join(DEFAULT_TOPIC_CODE_PATTERNS)}"
        ),
    )
    parser.add_argument(
        "--node-pattern",
        action="append",
        dest="node_patterns",
        help=(
            "Regex for micro_skill_nodes.node_id. Can be repeated. "
            f"Default: {', '.join(DEFAULT_NODE_ID_PATTERNS)}"
        ),
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    args = parse_args()
    settings = AppSettings.from_env()
    if not settings.database_url:
        raise SystemExit("DATABASE_URL is required for cleanup script")

    dry_run = not args.apply
    filters = FixtureCleanupFilters(
        subject_code_patterns=tuple(
            args.subject_patterns or DEFAULT_SUBJECT_CODE_PATTERNS
        ),
        topic_code_patterns=tuple(args.topic_patterns or DEFAULT_TOPIC_CODE_PATTERNS),
        node_id_patterns=tuple(args.node_patterns or DEFAULT_NODE_ID_PATTERNS),
    )

    logger.info(
        (
            "metric=assessment_fixture_cleanup_runs_total "
            "status=started value=1 dry_run=%s"
        ),
        str(dry_run).lower(),
    )
    result = run_fixture_cleanup(uow=build_uow(), dry_run=dry_run, filters=filters)
    logger.info(
        (
            "metric=assessment_fixture_cleanup_runs_total "
            "status=succeeded value=1 dry_run=%s"
        ),
        str(dry_run).lower(),
    )
    print(
        json.dumps(
            {
                "status": "planned" if result.dry_run else "completed",
                "dry_run": result.dry_run,
                "filters": {
                    "subject_code_patterns": list(result.filters.subject_code_patterns),
                    "topic_code_patterns": list(result.filters.topic_code_patterns),
                    "node_id_patterns": list(result.filters.node_id_patterns),
                },
                "matched": result.matched.__dict__,
                "deleted": result.deleted.__dict__,
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception(
            "metric=assessment_fixture_cleanup_runs_total status=failed value=1"
        )
        raise
