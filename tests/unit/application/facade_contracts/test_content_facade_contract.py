from __future__ import annotations

from src.application.facade import CleanupFixturesInput
from src.infrastructure.uow import InMemoryUnitOfWork

from .support import build_content_facade, seed_basic_catalog


def test_content_facade_contract() -> None:
    uow = InMemoryUnitOfWork()
    facade = build_content_facade(uow)

    assignment_id, child_id = seed_basic_catalog(facade)

    assert len(facade.list_subjects()) == 1
    assert len(facade.list_topics()) == 1
    assert len(facade.list_micro_skills()) == 1
    assert len(facade.list_tests()) == 1

    assignments = uow.assignments.list_by_child(child_id)
    assert assignments[0].assignment_id == assignment_id

    cleanup_result = facade.cleanup_fixtures(
        payload=CleanupFixturesInput(
            dry_run=True,
            subject_code_patterns=("^math$",),
            topic_code_patterns=("^MATH",),
            node_id_patterns=("^MATH",),
        )
    )
    assert cleanup_result.dry_run is True
