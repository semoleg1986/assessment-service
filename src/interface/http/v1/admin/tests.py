from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status

from src.application.errors import InvariantViolationError, NotFoundError
from src.application.facade import AssessmentContentFacade
from src.interface.http.policies import with_error_mapping
from src.interface.http.v1.mappers import to_create_test_input
from src.interface.http.v1.admin._helpers import test_response
from src.interface.http.v1.schemas import (
    CreateTestRequest,
    PublishTestResponse,
    TestResponse,
)

router = APIRouter(tags=["assessment"], route_class=DishkaRoute)


@router.post("/tests", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
@router.post(
    "/admin/tests",
    response_model=TestResponse,
    status_code=status.HTTP_201_CREATED,
)
@with_error_mapping((NotFoundError, 404), (InvariantViolationError, 409))
def create_test(
    body: CreateTestRequest,
    facade: FromDishka[AssessmentContentFacade],
) -> TestResponse:
    test = facade.create_test(payload=to_create_test_input(body))

    return test_response(test)


@router.get("/tests", response_model=list[TestResponse])
@router.get("/admin/tests", response_model=list[TestResponse])
def list_tests(
    facade: FromDishka[AssessmentContentFacade],
) -> list[TestResponse]:
    tests = facade.list_tests()
    return [test_response(test) for test in tests]


@router.post(
    "/admin/tests/{test_id}/publish",
    response_model=PublishTestResponse,
)
def publish_test(
    test_id: UUID,
    facade: FromDishka[AssessmentContentFacade],
) -> PublishTestResponse:
    if facade.get_test_by_id(test_id=test_id) is None:
        raise HTTPException(status_code=404, detail="test not found")
    return PublishTestResponse(test_id=test_id, status="published")
