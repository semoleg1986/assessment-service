from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, TypedDict

from src.application.ports.unit_of_work import UnitOfWork
from src.application.reporting.handlers.get_child_skill_results import (
    handle_get_child_skill_results,
)
from src.application.reporting.queries.get_child_correction_plan import (
    GetChildCorrectionPlanQuery,
)
from src.application.reporting.queries.get_child_skill_results import (
    GetChildSkillResultsQuery,
)
from src.domain.shared.signals import SkillSignal

CorrectionPriority = Literal["P1", "P2", "P3", "P4"]

_SIGNAL_TO_PRIORITY: dict[SkillSignal, CorrectionPriority] = {
    SkillSignal.CRITICAL_GAP: "P1",
    SkillSignal.GAP: "P2",
    SkillSignal.RISK: "P3",
    SkillSignal.NORMAL: "P4",
}


class CorrectionPlanAction(TypedDict):
    node_id: str
    topic_code: str | None
    skill_name: str
    signal: SkillSignal
    priority: CorrectionPriority
    rationale: str
    recommendation: str
    target_outcome: str


class ChildCorrectionPlanSummary(TypedDict):
    actions_total: int
    p1_total: int
    p2_total: int
    p3_total: int
    p4_total: int


class ChildCorrectionPlan(TypedDict):
    child_id: str
    generated_at: datetime
    summary: ChildCorrectionPlanSummary
    actions: list[CorrectionPlanAction]


def _target_outcome(*, signal: SkillSignal) -> str:
    if signal == SkillSignal.CRITICAL_GAP:
        return "Довести до signal=gap или risk за 1-2 учебных цикла."
    if signal == SkillSignal.GAP:
        return "Довести до signal=risk в ближайший учебный цикл."
    if signal == SkillSignal.RISK:
        return "Стабилизировать и выйти в signal=normal."
    return "Поддерживающая практика без срочных коррекций."


def handle_get_child_correction_plan(
    query: GetChildCorrectionPlanQuery,
    *,
    uow: UnitOfWork,
) -> ChildCorrectionPlan:
    skill_results = handle_get_child_skill_results(
        GetChildSkillResultsQuery(child_id=query.child_id),
        uow=uow,
    )

    actions: list[CorrectionPlanAction] = []
    p1_total = 0
    p2_total = 0
    p3_total = 0
    p4_total = 0

    for skill in skill_results["skills"]:
        signal = skill["signal"]
        priority = _SIGNAL_TO_PRIORITY[signal]
        if priority == "P1":
            p1_total += 1
        elif priority == "P2":
            p2_total += 1
        elif priority == "P3":
            p3_total += 1
        else:
            p4_total += 1

        actions.append(
            {
                "node_id": skill["node_id"],
                "topic_code": skill["topic_code"],
                "skill_name": skill["skill_name"],
                "signal": signal,
                "priority": priority,
                "rationale": (
                    "accuracy="
                    f"{skill['accuracy_percent']}%, "
                    f"wilson_low={skill['wilson_low']}"
                ),
                "recommendation": skill["recommendation"],
                "target_outcome": _target_outcome(signal=signal),
            }
        )

    return {
        "child_id": str(query.child_id),
        "generated_at": datetime.now(timezone.utc),
        "summary": {
            "actions_total": len(actions),
            "p1_total": p1_total,
            "p2_total": p2_total,
            "p3_total": p3_total,
            "p4_total": p4_total,
        },
        "actions": actions,
    }
