from collections import Counter
from datetime import datetime
from typing import TypedDict

from src.application.ports.unit_of_work import UnitOfWork
from src.application.reporting.queries.get_child_results import GetChildResultsQuery
from src.domain.delivery.attempt.aggregate import AttemptAggregate
from src.domain.shared.statuses import AttemptStatus


class ChildResultsAttempt(TypedDict):
    attempt_id: str
    assignment_id: str
    status: str
    score: int
    started_at: datetime
    submitted_at: datetime | None
    duration_seconds: int | None
    answers_total: int
    expected_answers_total: int
    unanswered_answers_total: int
    correct_answers: int
    accuracy_percent: float
    time_spent_ms_total: int
    avg_time_per_answer_ms: int | None
    has_resolved_diagnostics: bool
    resolved_diagnostic_tags: dict[str, int]


class ChildResultsSummary(TypedDict):
    attempts_total: int
    submitted_attempts_total: int
    started_attempts_total: int
    attempts_with_diagnostics_total: int
    answers_total: int
    expected_answers_total: int
    correct_answers_total: int
    accuracy_percent: float
    time_spent_ms_total: int
    avg_time_per_answer_ms: int | None
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
    assignments_by_id = {
        assignment.assignment_id: assignment
        for assignment in uow.assignments.list_by_child(query.child_id)
    }
    expected_answers_cache: dict[str, int] = {}

    summary_tags: Counter[str] = Counter()
    attempt_rows: list[ChildResultsAttempt] = []
    submitted_attempts_total = 0
    started_attempts_total = 0
    attempts_with_diagnostics_total = 0
    answers_total = 0
    expected_answers_total = 0
    correct_answers_total = 0
    time_spent_ms_total = 0

    for attempt in attempts:
        if attempt.status == AttemptStatus.SUBMITTED:
            submitted_attempts_total += 1
        if attempt.status == AttemptStatus.STARTED:
            started_attempts_total += 1

        assignment = assignments_by_id.get(attempt.assignment_id)
        expected_count = len(attempt.answers)
        if assignment is not None:
            test_id_key = str(assignment.test_id)
            if test_id_key in expected_answers_cache:
                expected_count = expected_answers_cache[test_id_key]
            else:
                test = uow.tests.get(assignment.test_id)
                if test is not None:
                    expected_count = len(test.questions)
                expected_answers_cache[test_id_key] = expected_count

        attempt_tags: Counter[str] = Counter()
        correct_answers = 0
        answered_total = len(attempt.answers)
        unanswered_total = max(expected_count - answered_total, 0)
        attempt_time_spent_ms_total = 0
        for answer in attempt.answers:
            if answer.is_correct:
                correct_answers += 1
            if answer.time_spent_ms is not None:
                attempt_time_spent_ms_total += max(answer.time_spent_ms, 0)
            if answer.resolved_diagnostic_tag is not None:
                tag = answer.resolved_diagnostic_tag.value
                attempt_tags[tag] += 1
                summary_tags[tag] += 1

        if attempt_tags:
            attempts_with_diagnostics_total += 1

        answers_total += answered_total
        expected_answers_total += expected_count
        correct_answers_total += correct_answers
        time_spent_ms_total += attempt_time_spent_ms_total

        accuracy_percent = (
            round((correct_answers / expected_count) * 100, 2)
            if expected_count > 0
            else 0.0
        )
        avg_time_per_answer_ms = (
            int(round(attempt_time_spent_ms_total / answered_total))
            if answered_total > 0
            else None
        )
        duration_seconds = (
            max(int((attempt.submitted_at - attempt.started_at).total_seconds()), 0)
            if attempt.submitted_at is not None
            else None
        )

        attempt_rows.append(
            {
                "attempt_id": str(attempt.attempt_id),
                "assignment_id": str(attempt.assignment_id),
                "status": attempt.status.value,
                "score": attempt.score,
                "started_at": attempt.started_at,
                "submitted_at": attempt.submitted_at,
                "duration_seconds": duration_seconds,
                "answers_total": answered_total,
                "expected_answers_total": expected_count,
                "unanswered_answers_total": unanswered_total,
                "correct_answers": correct_answers,
                "accuracy_percent": accuracy_percent,
                "time_spent_ms_total": attempt_time_spent_ms_total,
                "avg_time_per_answer_ms": avg_time_per_answer_ms,
                "has_resolved_diagnostics": bool(attempt_tags),
                "resolved_diagnostic_tags": dict(attempt_tags),
            }
        )

    summary_accuracy_percent = (
        round((correct_answers_total / expected_answers_total) * 100, 2)
        if expected_answers_total > 0
        else 0.0
    )
    summary_avg_time_per_answer_ms = (
        int(round(time_spent_ms_total / answers_total)) if answers_total > 0 else None
    )

    return {
        "child_id": str(query.child_id),
        "summary": {
            "attempts_total": len(attempts),
            "submitted_attempts_total": submitted_attempts_total,
            "started_attempts_total": started_attempts_total,
            "attempts_with_diagnostics_total": attempts_with_diagnostics_total,
            "answers_total": answers_total,
            "expected_answers_total": expected_answers_total,
            "correct_answers_total": correct_answers_total,
            "accuracy_percent": summary_accuracy_percent,
            "time_spent_ms_total": time_spent_ms_total,
            "avg_time_per_answer_ms": summary_avg_time_per_answer_ms,
            "resolved_diagnostic_tags": dict(summary_tags),
        },
        "attempts": attempt_rows,
    }
