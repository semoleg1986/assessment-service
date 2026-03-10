from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.application.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class FixtureCleanupFilters:
    subject_code_patterns: tuple[str, ...]
    topic_code_patterns: tuple[str, ...]
    node_id_patterns: tuple[str, ...]


@dataclass(frozen=True)
class FixtureCleanupCounts:
    subjects: int = 0
    topics: int = 0
    micro_skills: int = 0
    tests: int = 0
    questions: int = 0
    assignments: int = 0
    attempts: int = 0
    answers: int = 0


@dataclass(frozen=True)
class FixtureCleanupExecution:
    dry_run: bool
    filters: FixtureCleanupFilters
    matched: FixtureCleanupCounts
    deleted: FixtureCleanupCounts


class FixtureCleanupUnsupportedError(RuntimeError):
    pass


class FixtureCleanupService(Protocol):
    def run(
        self,
        *,
        uow: UnitOfWork,
        dry_run: bool,
        filters: FixtureCleanupFilters,
    ) -> FixtureCleanupExecution: ...
