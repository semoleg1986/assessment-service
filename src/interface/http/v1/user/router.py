from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from src.application.contracts.questions import DiagnosticTag
from src.application.errors import InvariantViolationError, NotFoundError
from src.application.facade import AssessmentUserFacade
from src.interface.http.policies import with_error_mapping
from src.interface.http.v1.mappers import (
    to_attempt_id_input,
    to_child_scoped_input,
    to_save_attempt_answers_input,
    to_start_attempt_input,
    to_submit_attempt_input,
)
from src.interface.http.v1.schemas import (
    AssignmentListItemResponse,
    AttemptAnswerResponse,
    AttemptResultResponse,
    SaveAttemptAnswersRequest,
    SaveAttemptAnswersResponse,
    StartAttemptByAssignmentRequest,
    StartAttemptRequest,
    StartAttemptResponse,
    SubmitAttemptRequest,
    SubmitAttemptResponse,
)

router = APIRouter(tags=["assessment"], route_class=DishkaRoute)


@router.get(
    "/user/children/{child_id}/assignments",
    response_model=list[AssignmentListItemResponse],
)
def list_assignments_by_child(
    child_id: UUID,
    facade: FromDishka[AssessmentUserFacade],
) -> list[AssignmentListItemResponse]:
    assignments = facade.list_assignments_by_child(
        payload=to_child_scoped_input(child_id=child_id)
    )
    return [
        AssignmentListItemResponse(
            assignment_id=a.assignment_id,
            test_id=a.test_id,
            status=a.status.value,
            attempt_no=a.attempt_no,
        )
        for a in assignments
    ]


@router.post("/attempts/start", response_model=StartAttemptResponse)
@with_error_mapping((NotFoundError, 404), (InvariantViolationError, 409))
def start_attempt(
    body: StartAttemptRequest,
    facade: FromDishka[AssessmentUserFacade],
) -> StartAttemptResponse:
    attempt = facade.start_attempt(payload=to_start_attempt_input(body))

    return StartAttemptResponse(
        attempt_id=attempt.attempt_id,
        assignment_id=attempt.assignment_id,
        child_id=attempt.child_id,
        status=attempt.status.value,
    )


@router.post(
    "/user/assignments/{assignment_id}/start",
    response_model=StartAttemptResponse,
)
def start_attempt_for_assignment(
    assignment_id: UUID,
    body: StartAttemptByAssignmentRequest,
    facade: FromDishka[AssessmentUserFacade],
) -> StartAttemptResponse:
    return start_attempt(
        StartAttemptRequest(assignment_id=assignment_id, child_id=body.child_id),
        facade=facade,
    )


@router.post(
    "/attempts/{attempt_id}/submit",
    response_model=SubmitAttemptResponse,
)
@router.post(
    "/user/attempts/{attempt_id}/submit",
    response_model=SubmitAttemptResponse,
)
@with_error_mapping((NotFoundError, 404), (InvariantViolationError, 409))
def submit_attempt(
    attempt_id: UUID,
    body: SubmitAttemptRequest,
    facade: FromDishka[AssessmentUserFacade],
) -> SubmitAttemptResponse:
    result = facade.submit_attempt(
        payload=to_submit_attempt_input(attempt_id=attempt_id, body=body)
    )

    return SubmitAttemptResponse(**result)


@router.post(
    "/user/attempts/{attempt_id}/answers",
    response_model=SaveAttemptAnswersResponse,
)
@with_error_mapping((NotFoundError, 404), (InvariantViolationError, 409))
def save_attempt_answers(
    attempt_id: UUID,
    body: SaveAttemptAnswersRequest,
    facade: FromDishka[AssessmentUserFacade],
) -> SaveAttemptAnswersResponse:
    result = facade.save_attempt_answers(
        payload=to_save_attempt_answers_input(attempt_id=attempt_id, body=body)
    )
    return SaveAttemptAnswersResponse(
        attempt_id=str(result["attempt_id"]),
        saved_answers=int(result["saved_answers"]),
    )


@router.get("/attempts/{attempt_id}", response_model=AttemptResultResponse)
@with_error_mapping((NotFoundError, 404))
def get_attempt_result(
    attempt_id: UUID,
    facade: FromDishka[AssessmentUserFacade],
) -> AttemptResultResponse:
    result = facade.get_attempt_result(
        payload=to_attempt_id_input(attempt_id=attempt_id)
    )
    return AttemptResultResponse(
        attempt_id=result["attempt_id"],
        status=result["status"],
        score=result["score"],
        answers=[
            AttemptAnswerResponse(
                question_id=a["question_id"],
                value=a["value"],
                selected_option_id=a["selected_option_id"],
                resolved_diagnostic_tag=(
                    DiagnosticTag(a["resolved_diagnostic_tag"])
                    if a["resolved_diagnostic_tag"] is not None
                    else None
                ),
                time_spent_ms=a["time_spent_ms"],
                is_correct=a["is_correct"],
                awarded_score=a["awarded_score"],
            )
            for a in result["answers"]
        ],
    )


@router.get(
    "/user/attempts/{attempt_id}/result",
    response_model=AttemptResultResponse,
)
def get_attempt_result_for_user(
    attempt_id: UUID,
    facade: FromDishka[AssessmentUserFacade],
) -> AttemptResultResponse:
    return get_attempt_result(attempt_id, facade=facade)
