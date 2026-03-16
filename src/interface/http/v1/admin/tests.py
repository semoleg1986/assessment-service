from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status

from src.application.content.commands.create_test import (
    CreateTestCommand,
    QuestionInput,
    QuestionOptionInput,
    TextDistractorInput,
)
from src.application.content.handlers.create_test import handle_create_test
from src.application.content.handlers.get_test_by_id import handle_get_test_by_id
from src.application.content.handlers.list_tests import handle_list_tests
from src.application.content.queries.get_test_by_id import GetTestByIdQuery
from src.application.content.queries.list_tests import ListTestsQuery
from src.application.errors import InvariantViolationError, NotFoundError
from src.application.ports.unit_of_work import UnitOfWork
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
def create_test(
    body: CreateTestRequest,
    uow: FromDishka[UnitOfWork],
) -> TestResponse:
    try:
        test = handle_create_test(
            CreateTestCommand(
                subject_code=body.subject_code,
                grade=body.grade,
                questions=[
                    QuestionInput(
                        node_id=question.node_id,
                        text=question.text,
                        question_type=question.question_type,
                        answer_key=question.answer_key,
                        correct_option_id=question.correct_option_id,
                        options=[
                            QuestionOptionInput(
                                option_id=option.option_id,
                                text=option.text,
                                position=option.position,
                                diagnostic_tag=option.diagnostic_tag,
                            )
                            for option in question.options
                        ],
                        text_distractors=[
                            TextDistractorInput(
                                pattern=distractor.pattern,
                                match_mode=distractor.match_mode,
                                diagnostic_tag=distractor.diagnostic_tag,
                            )
                            for distractor in question.text_distractors
                        ],
                        max_score=question.max_score,
                    )
                    for question in body.questions
                ],
            ),
            uow=uow,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return test_response(test)


@router.get("/tests", response_model=list[TestResponse])
@router.get("/admin/tests", response_model=list[TestResponse])
def list_tests(
    uow: FromDishka[UnitOfWork],
) -> list[TestResponse]:
    tests = handle_list_tests(ListTestsQuery(), uow=uow)
    return [test_response(test) for test in tests]


@router.post(
    "/admin/tests/{test_id}/publish",
    response_model=PublishTestResponse,
)
def publish_test(
    test_id: UUID,
    uow: FromDishka[UnitOfWork],
) -> PublishTestResponse:
    if handle_get_test_by_id(GetTestByIdQuery(test_id=test_id), uow=uow) is None:
        raise HTTPException(status_code=404, detail="test not found")
    return PublishTestResponse(test_id=test_id, status="published")
