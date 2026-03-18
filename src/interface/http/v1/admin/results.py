from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from src.application.facade import AssessmentAdminFacade
from src.interface.http.v1.admin._helpers import sorted_diagnostic_tag_counts
from src.interface.http.v1.schemas import (
    ChildDiagnosticsResponse,
    ChildResultsAttemptResponse,
    ChildResultsResponse,
    ChildResultsSummaryResponse,
    ChildSkillResultResponse,
    ChildSkillResultsResponse,
    ChildSkillResultsSummaryResponse,
)

router = APIRouter(tags=["assessment"], route_class=DishkaRoute)


@router.get(
    "/admin/diagnostics/children/{child_id}",
    response_model=ChildDiagnosticsResponse,
)
def get_child_diagnostics(
    child_id: UUID,
    facade: FromDishka[AssessmentAdminFacade],
) -> ChildDiagnosticsResponse:
    result = facade.get_child_diagnostics(child_id=child_id)
    return ChildDiagnosticsResponse(
        child_id=child_id,
        assignments_total=result["assignments_total"],
        attempts_total=result["attempts_total"],
    )


@router.get(
    "/admin/results/children/{child_id}",
    response_model=ChildResultsResponse,
)
def get_child_results(
    child_id: UUID,
    facade: FromDishka[AssessmentAdminFacade],
) -> ChildResultsResponse:
    result = facade.get_child_results(child_id=child_id)
    return ChildResultsResponse(
        child_id=child_id,
        summary=ChildResultsSummaryResponse(
            attempts_total=result["summary"]["attempts_total"],
            submitted_attempts_total=result["summary"]["submitted_attempts_total"],
            started_attempts_total=result["summary"]["started_attempts_total"],
            attempts_with_diagnostics_total=result["summary"][
                "attempts_with_diagnostics_total"
            ],
            answers_total=result["summary"]["answers_total"],
            expected_answers_total=result["summary"]["expected_answers_total"],
            correct_answers_total=result["summary"]["correct_answers_total"],
            accuracy_percent=result["summary"]["accuracy_percent"],
            time_spent_ms_total=result["summary"]["time_spent_ms_total"],
            avg_time_per_answer_ms=result["summary"]["avg_time_per_answer_ms"],
            resolved_diagnostic_tags=sorted_diagnostic_tag_counts(
                result["summary"]["resolved_diagnostic_tags"]
            ),
        ),
        attempts=[
            ChildResultsAttemptResponse(
                attempt_id=item["attempt_id"],
                assignment_id=item["assignment_id"],
                status=item["status"],
                score=item["score"],
                started_at=item["started_at"],
                submitted_at=item["submitted_at"],
                duration_seconds=item["duration_seconds"],
                answers_total=item["answers_total"],
                expected_answers_total=item["expected_answers_total"],
                unanswered_answers_total=item["unanswered_answers_total"],
                correct_answers=item["correct_answers"],
                accuracy_percent=item["accuracy_percent"],
                time_spent_ms_total=item["time_spent_ms_total"],
                avg_time_per_answer_ms=item["avg_time_per_answer_ms"],
                has_resolved_diagnostics=item["has_resolved_diagnostics"],
                resolved_diagnostic_tags=sorted_diagnostic_tag_counts(
                    item["resolved_diagnostic_tags"]
                ),
            )
            for item in result["attempts"]
        ],
    )


@router.get(
    "/admin/results/children/{child_id}/skills",
    response_model=ChildSkillResultsResponse,
)
def get_child_skill_results(
    child_id: UUID,
    facade: FromDishka[AssessmentAdminFacade],
) -> ChildSkillResultsResponse:
    result = facade.get_child_skill_results(child_id=child_id)
    return ChildSkillResultsResponse(
        child_id=child_id,
        summary=ChildSkillResultsSummaryResponse(
            total_skills=result["summary"]["total_skills"],
            high_gap_total=result["summary"]["high_gap_total"],
            medium_gap_total=result["summary"]["medium_gap_total"],
            low_gap_total=result["summary"]["low_gap_total"],
            insufficient_data_total=result["summary"]["insufficient_data_total"],
        ),
        skills=[
            ChildSkillResultResponse(
                node_id=item["node_id"],
                topic_code=item["topic_code"],
                skill_name=item["skill_name"],
                attempted_questions=item["attempted_questions"],
                correct_answers=item["correct_answers"],
                accuracy_percent=item["accuracy_percent"],
                avg_time_per_answer_ms=item["avg_time_per_answer_ms"],
                wilson_low=item["wilson_low"],
                wilson_high=item["wilson_high"],
                gap_level=item["gap_level"],
                resolved_diagnostic_tags=sorted_diagnostic_tag_counts(
                    item["resolved_diagnostic_tags"]
                ),
                recommendation=item["recommendation"],
            )
            for item in result["skills"]
        ],
    )
