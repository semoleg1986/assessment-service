from collections import Counter
from dataclasses import dataclass, field
from math import sqrt
from typing import Literal, TypeAlias, TypedDict

from src.application.ports.unit_of_work import UnitOfWork
from src.application.reporting.queries.get_child_skill_results import (
    GetChildSkillResultsQuery,
)
from src.domain.shared.questions import DiagnosticTag
from src.domain.shared.signals import SkillSignal

_WILSON_Z_95 = 1.96
_INSUFFICIENT_DATA_THRESHOLD = 3
_HIGH_GAP_WILSON_LOW_THRESHOLD = 0.60
_MEDIUM_GAP_WILSON_LOW_THRESHOLD = 0.75

_DIAGNOSTIC_RECOMMENDATIONS: dict[str, str] = {
    DiagnosticTag.CALC_ERROR.value: (
        "Разобрать вычисление по шагам и закрепить базовые операции."
    ),
    DiagnosticTag.MISREAD_CONDITION.value: (
        "Тренировать чтение условия: выделение данных и вопроса задачи."
    ),
    DiagnosticTag.INATTENTION.value: (
        "Добавить контрольный шаг проверки ответа перед отправкой."
    ),
    DiagnosticTag.CONCEPT_GAP.value: (
        "Повторить базовое правило и решить 3-5 опорных задач."
    ),
    DiagnosticTag.GUESSING.value: (
        "Требовать краткое объяснение выбора ответа перед фиксацией."
    ),
    DiagnosticTag.OTHER.value: "Разобрать ошибки вручную и уточнить паттерн.",
}

GapLevel: TypeAlias = Literal["insufficient_data", "high", "medium", "low"]

_GAP_LEVEL_RANK: dict[GapLevel, int] = {
    "high": 0,
    "medium": 1,
    "low": 2,
    "insufficient_data": 3,
}

_SIGNAL_RANK: dict[SkillSignal, int] = {
    SkillSignal.CRITICAL_GAP: 0,
    SkillSignal.GAP: 1,
    SkillSignal.RISK: 2,
    SkillSignal.NORMAL: 3,
}


class ChildSkillResult(TypedDict):
    node_id: str
    topic_code: str | None
    skill_name: str
    attempted_questions: int
    correct_answers: int
    accuracy_percent: float
    avg_time_per_answer_ms: int | None
    wilson_low: float
    wilson_high: float
    gap_level: GapLevel
    signal: SkillSignal
    resolved_diagnostic_tags: dict[str, int]
    recommendation: str


class ChildSkillResultsSummary(TypedDict):
    total_skills: int
    high_gap_total: int
    medium_gap_total: int
    low_gap_total: int
    insufficient_data_total: int
    critical_gap_total: int
    gap_total: int
    risk_total: int
    normal_total: int


class ChildSkillResults(TypedDict):
    child_id: str
    summary: ChildSkillResultsSummary
    skills: list[ChildSkillResult]


@dataclass(slots=True)
class _SkillAccumulator:
    topic_code: str | None
    skill_name: str
    attempted_questions: int = 0
    correct_answers: int = 0
    time_spent_ms_total: int = 0
    timed_answers_total: int = 0
    resolved_diagnostic_tags: Counter[str] = field(default_factory=Counter)


def _wilson_interval(
    correct_answers: int, attempted_questions: int
) -> tuple[float, float]:
    if attempted_questions <= 0:
        return 0.0, 1.0

    z = _WILSON_Z_95
    z_squared = z * z
    probability = correct_answers / attempted_questions
    denominator = 1 + z_squared / attempted_questions
    center = (probability + z_squared / (2 * attempted_questions)) / denominator
    margin = (
        z
        * sqrt(
            (probability * (1 - probability) + z_squared / (4 * attempted_questions))
            / attempted_questions
        )
        / denominator
    )
    return round(max(0.0, center - margin), 4), round(min(1.0, center + margin), 4)


def _gap_level(attempted_questions: int, wilson_low: float) -> GapLevel:
    if attempted_questions < _INSUFFICIENT_DATA_THRESHOLD:
        return "insufficient_data"
    if wilson_low < _HIGH_GAP_WILSON_LOW_THRESHOLD:
        return "high"
    if wilson_low < _MEDIUM_GAP_WILSON_LOW_THRESHOLD:
        return "medium"
    return "low"


def _top_diagnostic_tag(tag_counts: Counter[str]) -> str | None:
    if not tag_counts:
        return None
    return sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _signal(
    *,
    attempted_questions: int,
    accuracy_percent: float,
    wilson_low: float,
    gap_level: GapLevel,
) -> SkillSignal:
    del attempted_questions, accuracy_percent, wilson_low
    if gap_level == "high":
        return SkillSignal.CRITICAL_GAP
    if gap_level == "medium":
        return SkillSignal.GAP
    if gap_level == "low":
        return SkillSignal.NORMAL
    if gap_level == "insufficient_data":
        return SkillSignal.RISK
    return SkillSignal.RISK


def _recommendation(
    *,
    gap_level: GapLevel,
    top_diagnostic_tag: str | None,
    skill_name: str,
) -> str:
    if gap_level == "insufficient_data":
        return "Недостаточно данных для вывода по навыку. Нужны минимум 3 ответа."

    if top_diagnostic_tag is None:
        if gap_level == "low":
            return "Навык стабилен. Поддерживать практикой 1-2 задачи в неделю."
        return f"Требуется дополнительная практика по навыку: {skill_name}."

    recommendation_core = _DIAGNOSTIC_RECOMMENDATIONS.get(
        top_diagnostic_tag,
        _DIAGNOSTIC_RECOMMENDATIONS[DiagnosticTag.OTHER.value],
    )
    if gap_level == "high":
        return f"Высокий приоритет. {recommendation_core}"
    if gap_level == "medium":
        return f"Средний приоритет. {recommendation_core}"
    return f"Поддерживающая практика. {recommendation_core}"


def handle_get_child_skill_results(
    query: GetChildSkillResultsQuery,
    *,
    uow: UnitOfWork,
) -> ChildSkillResults:
    attempts = uow.attempts.list_by_child(query.child_id)
    assignments_by_id = {
        assignment.assignment_id: assignment
        for assignment in uow.assignments.list_by_child(query.child_id)
    }
    micro_skills_by_node_id = {
        micro_skill.node_id: micro_skill for micro_skill in uow.micro_skills.list()
    }

    question_to_node_by_test_id: dict[str, dict[str, str]] = {}
    skill_accumulators: dict[str, _SkillAccumulator] = {}

    for attempt in attempts:
        assignment = assignments_by_id.get(attempt.assignment_id)
        if assignment is None:
            continue

        test_id_key = str(assignment.test_id)
        if test_id_key not in question_to_node_by_test_id:
            test = uow.tests.get(assignment.test_id)
            if test is None:
                question_to_node_by_test_id[test_id_key] = {}
            else:
                question_to_node_by_test_id[test_id_key] = {
                    str(question.question_id): question.node_id
                    for question in test.questions
                }
        question_to_node = question_to_node_by_test_id[test_id_key]

        for answer in attempt.answers:
            node_id = question_to_node.get(str(answer.question_id))
            if node_id is None:
                continue

            accumulator = skill_accumulators.get(node_id)
            if accumulator is None:
                micro_skill = micro_skills_by_node_id.get(node_id)
                accumulator = _SkillAccumulator(
                    topic_code=(
                        micro_skill.topic_code if micro_skill is not None else None
                    ),
                    skill_name=(
                        micro_skill.micro_skill_name
                        if micro_skill is not None
                        else node_id
                    ),
                )
                skill_accumulators[node_id] = accumulator

            accumulator.attempted_questions += 1
            if answer.is_correct:
                accumulator.correct_answers += 1
            if answer.time_spent_ms is not None:
                accumulator.time_spent_ms_total += max(answer.time_spent_ms, 0)
                accumulator.timed_answers_total += 1
            if answer.resolved_diagnostic_tag is not None:
                accumulator.resolved_diagnostic_tags[
                    answer.resolved_diagnostic_tag.value
                ] += 1

    rows: list[ChildSkillResult] = []
    high_gap_total = 0
    medium_gap_total = 0
    low_gap_total = 0
    insufficient_data_total = 0
    critical_gap_total = 0
    gap_total = 0
    risk_total = 0
    normal_total = 0

    for node_id, accumulator in skill_accumulators.items():
        attempted_questions = accumulator.attempted_questions
        correct_answers = accumulator.correct_answers
        accuracy_percent = (
            round((correct_answers / attempted_questions) * 100, 2)
            if attempted_questions > 0
            else 0.0
        )
        avg_time_per_answer_ms = (
            int(
                round(accumulator.time_spent_ms_total / accumulator.timed_answers_total)
            )
            if accumulator.timed_answers_total > 0
            else None
        )
        wilson_low, wilson_high = _wilson_interval(correct_answers, attempted_questions)
        gap_level = _gap_level(attempted_questions, wilson_low)
        signal = _signal(
            attempted_questions=attempted_questions,
            accuracy_percent=accuracy_percent,
            wilson_low=wilson_low,
            gap_level=gap_level,
        )

        if gap_level == "high":
            high_gap_total += 1
        elif gap_level == "medium":
            medium_gap_total += 1
        elif gap_level == "low":
            low_gap_total += 1
        else:
            insufficient_data_total += 1

        if signal == SkillSignal.CRITICAL_GAP:
            critical_gap_total += 1
        elif signal == SkillSignal.GAP:
            gap_total += 1
        elif signal == SkillSignal.RISK:
            risk_total += 1
        else:
            normal_total += 1

        top_diagnostic_tag = _top_diagnostic_tag(accumulator.resolved_diagnostic_tags)
        rows.append(
            {
                "node_id": node_id,
                "topic_code": accumulator.topic_code,
                "skill_name": accumulator.skill_name,
                "attempted_questions": attempted_questions,
                "correct_answers": correct_answers,
                "accuracy_percent": accuracy_percent,
                "avg_time_per_answer_ms": avg_time_per_answer_ms,
                "wilson_low": wilson_low,
                "wilson_high": wilson_high,
                "gap_level": gap_level,
                "signal": signal,
                "resolved_diagnostic_tags": dict(accumulator.resolved_diagnostic_tags),
                "recommendation": _recommendation(
                    gap_level=gap_level,
                    top_diagnostic_tag=top_diagnostic_tag,
                    skill_name=accumulator.skill_name,
                ),
            }
        )

    rows.sort(
        key=lambda row: (
            _SIGNAL_RANK[row["signal"]],
            _GAP_LEVEL_RANK[row["gap_level"]],
            row["accuracy_percent"],
            row["skill_name"],
        )
    )

    return {
        "child_id": str(query.child_id),
        "summary": {
            "total_skills": len(rows),
            "high_gap_total": high_gap_total,
            "medium_gap_total": medium_gap_total,
            "low_gap_total": low_gap_total,
            "insufficient_data_total": insufficient_data_total,
            "critical_gap_total": critical_gap_total,
            "gap_total": gap_total,
            "risk_total": risk_total,
            "normal_total": normal_total,
        },
        "skills": rows,
    }
