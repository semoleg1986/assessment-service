from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status

from src.application.delivery.commands.assign_test import AssignTestCommand
from src.application.delivery.handlers.assign_test import handle_assign_test
from src.application.errors import InvariantViolationError, NotFoundError
from src.application.ports.unit_of_work import UnitOfWork
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
    uow: FromDishka[UnitOfWork],
) -> AssignmentResponse:
    try:
        assignment = handle_assign_test(
            AssignTestCommand(
                test_id=body.test_id,
                child_id=body.child_id,
                retake=body.retake,
            ),
            uow=uow,
        )
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
