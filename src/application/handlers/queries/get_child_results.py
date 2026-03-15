from collections import Counter
from datetime import datetime
from typing import TypedDict

from src.application.ports.unit_of_work import UnitOfWork
from src.application.queries.get_child_results import GetChildResultsQuery
from src.domain.aggregates.attempt import AttemptAggregate


class ChildResultsAttempt(TypedDict):
    attempt_id: str
    assignment_id: str
    status: str
    score: int
    started_at: datetime
    submitted_at: datetime | None
    answers_total: int
    correct_answers: int
    resolved_diagnostic_tags: dict[str, int]


class ChildResultsSummary(TypedDict):
    attempts_total: int
    submitted_attempts_total: int
    resolved_diagnostic_tags: dict[str, int]


class ChildResults(TypedDict):
    child_id: str
    summary: ChildResultsSummary
    attempts: list[ChildResultsAttempt]


def _attempt_sort_key(attempt: AttemptAggregate) -> str:
    timestamp = attempt.submitted_at or attempt.started_at
    return timestamp.isoformat()


def handle_get_child_results(
    query: GetChildResultsQuery,
    *,
    uow: UnitOfWork,
) -> ChildResults:
    attempts = sorted(
        uow.attempts.list_by_child(query.child_id),
        key=_attempt_sort_key,
        reverse=True,
    )

    summary_tags: Counter[str] = Counter()
    attempt_rows: list[ChildResultsAttempt] = []
    submitted_attempts_total = 0

    for attempt in attempts:
        if attempt.submitted_at is not None:
            submitted_attempts_total += 1

        attempt_tags: Counter[str] = Counter()
        correct_answers = 0
        for answer in attempt.answers:
            if answer.is_correct:
                correct_answers += 1
            if answer.resolved_diagnostic_tag is not None:
                tag = answer.resolved_diagnostic_tag.value
                attempt_tags[tag] += 1
                summary_tags[tag] += 1

        attempt_rows.append(
            {
                "attempt_id": str(attempt.attempt_id),
                "assignment_id": str(attempt.assignment_id),
                "status": attempt.status.value,
                "score": attempt.score,
                "started_at": attempt.started_at,
                "submitted_at": attempt.submitted_at,
                "answers_total": len(attempt.answers),
                "correct_answers": correct_answers,
                "resolved_diagnostic_tags": dict(attempt_tags),
            }
        )

    return {
        "child_id": str(query.child_id),
        "summary": {
            "attempts_total": len(attempts),
            "submitted_attempts_total": submitted_attempts_total,
            "resolved_diagnostic_tags": dict(summary_tags),
        },
        "attempts": attempt_rows,
    }
