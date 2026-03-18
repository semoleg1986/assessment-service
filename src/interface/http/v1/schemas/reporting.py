from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from src.application.contracts.questions import DiagnosticTag
from src.domain.shared.signals import SkillSignal


class ChildDiagnosticsResponse(BaseModel):
    child_id: UUID
    assignments_total: int
    attempts_total: int


class ChildResultsDiagnosticTagCountResponse(BaseModel):
    tag: DiagnosticTag
    count: int


class ChildResultsAttemptResponse(BaseModel):
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
    resolved_diagnostic_tags: list[ChildResultsDiagnosticTagCountResponse] = Field(
        default_factory=list
    )


class ChildResultsSummaryResponse(BaseModel):
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
    resolved_diagnostic_tags: list[ChildResultsDiagnosticTagCountResponse] = Field(
        default_factory=list
    )


class ChildResultsResponse(BaseModel):
    child_id: UUID
    summary: ChildResultsSummaryResponse
    attempts: list[ChildResultsAttemptResponse] = Field(default_factory=list)


class ChildSkillResultResponse(BaseModel):
    node_id: str
    topic_code: str | None
    skill_name: str
    attempted_questions: int
    correct_answers: int
    accuracy_percent: float
    avg_time_per_answer_ms: int | None
    wilson_low: float
    wilson_high: float
    gap_level: Literal["insufficient_data", "high", "medium", "low"]
    signal: SkillSignal
    resolved_diagnostic_tags: list[ChildResultsDiagnosticTagCountResponse] = Field(
        default_factory=list
    )
    recommendation: str


class ChildSkillResultsSummaryResponse(BaseModel):
    total_skills: int
    high_gap_total: int
    medium_gap_total: int
    low_gap_total: int
    insufficient_data_total: int
    critical_gap_total: int
    gap_total: int
    risk_total: int
    normal_total: int


class ChildSkillResultsResponse(BaseModel):
    child_id: UUID
    summary: ChildSkillResultsSummaryResponse
    skills: list[ChildSkillResultResponse] = Field(default_factory=list)


class ChildCorrectionPlanActionResponse(BaseModel):
    node_id: str
    topic_code: str | None
    skill_name: str
    signal: SkillSignal
    priority: Literal["P1", "P2", "P3", "P4"]
    rationale: str
    recommendation: str
    target_outcome: str


class ChildCorrectionPlanSummaryResponse(BaseModel):
    actions_total: int
    p1_total: int
    p2_total: int
    p3_total: int
    p4_total: int


class ChildCorrectionPlanResponse(BaseModel):
    child_id: UUID
    generated_at: datetime
    summary: ChildCorrectionPlanSummaryResponse
    actions: list[ChildCorrectionPlanActionResponse] = Field(default_factory=list)
