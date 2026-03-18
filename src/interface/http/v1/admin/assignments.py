from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status

from src.application.errors import InvariantViolationError, NotFoundError
from src.application.facade import AssessmentContentFacade
from src.interface.http.v1.mappers import to_assign_test_input
from src.interface.http.v1.schemas import AssignmentResponse, AssignTestRequest

router = APIRouter(tags=["assessment"], route_class=DishkaRoute)


@router.post(
    "/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/admin/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_test(
    body: AssignTestRequest,
    facade: FromDishka[AssessmentContentFacade],
) -> AssignmentResponse:
    try:
        assignment = facade.assign_test(payload=to_assign_test_input(body))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return AssignmentResponse(
        assignment_id=assignment.assignment_id,
        test_id=assignment.test_id,
        child_id=assignment.child_id,
        status=assignment.status.value,
        attempt_no=assignment.attempt_no,
    )
