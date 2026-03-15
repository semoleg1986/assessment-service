from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException

from src.application.commands import (
    SaveAttemptAnswersCommand,
    StartAttemptCommand,
    SubmitAttemptCommand,
    SubmittedAnswerInput,
)
from src.application.handlers import (
    handle_get_attempt_result,
    handle_list_assignments_by_child,
    handle_save_attempt_answers,
    handle_start_attempt,
    handle_submit_attempt,
)
from src.application.ports.unit_of_work import UnitOfWork
from src.application.queries import GetAttemptResultQuery, ListAssignmentsByChildQuery
from src.domain.errors import InvariantViolationError, NotFoundError
from src.domain.shared.questions import DiagnosticTag
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
    uow: FromDishka[UnitOfWork],
) -> list[AssignmentListItemResponse]:
    assignments = handle_list_assignments_by_child(
        ListAssignmentsByChildQuery(child_id=child_id),
        uow=uow,
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
def start_attempt(
    body: StartAttemptRequest,
    uow: FromDishka[UnitOfWork],
) -> StartAttemptResponse:
    try:
        attempt = handle_start_attempt(
            StartAttemptCommand(
                assignment_id=body.assignment_id,
                child_id=body.child_id,
            ),
            uow=uow,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

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
    uow: FromDishka[UnitOfWork],
) -> StartAttemptResponse:
    return start_attempt(
        StartAttemptRequest(assignment_id=assignment_id, child_id=body.child_id),
        uow=uow,
    )


@router.post(
    "/attempts/{attempt_id}/submit",
    response_model=SubmitAttemptResponse,
)
@router.post(
    "/user/attempts/{attempt_id}/submit",
    response_model=SubmitAttemptResponse,
)
def submit_attempt(
    attempt_id: UUID,
    body: SubmitAttemptRequest,
    uow: FromDishka[UnitOfWork],
) -> SubmitAttemptResponse:
    try:
        result = handle_submit_attempt(
            SubmitAttemptCommand(
                attempt_id=attempt_id,
                answers=[
                    SubmittedAnswerInput(
                        question_id=a.question_id,
                        value=a.value,
                        selected_option_id=a.selected_option_id,
                        time_spent_ms=a.time_spent_ms,
                    )
                    for a in body.answers
                ],
            ),
            uow=uow,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return SubmitAttemptResponse(**result)


@router.post(
    "/user/attempts/{attempt_id}/answers",
    response_model=SaveAttemptAnswersResponse,
)
def save_attempt_answers(
    attempt_id: UUID,
    body: SaveAttemptAnswersRequest,
    uow: FromDishka[UnitOfWork],
) -> SaveAttemptAnswersResponse:
    try:
        result = handle_save_attempt_answers(
            SaveAttemptAnswersCommand(
                attempt_id=attempt_id,
                answers=[
                    SubmittedAnswerInput(
                        question_id=a.question_id,
                        value=a.value,
                        selected_option_id=a.selected_option_id,
                        time_spent_ms=a.time_spent_ms,
                    )
                    for a in body.answers
                ],
            ),
            uow=uow,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return SaveAttemptAnswersResponse(
        attempt_id=str(result["attempt_id"]),
        saved_answers=int(result["saved_answers"]),
    )


@router.get("/attempts/{attempt_id}", response_model=AttemptResultResponse)
def get_attempt_result(
    attempt_id: UUID,
    uow: FromDishka[UnitOfWork],
) -> AttemptResultResponse:
    try:
        result = handle_get_attempt_result(
            GetAttemptResultQuery(attempt_id=attempt_id),
            uow=uow,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
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
    uow: FromDishka[UnitOfWork],
) -> AttemptResultResponse:
    return get_attempt_result(attempt_id, uow=uow)
