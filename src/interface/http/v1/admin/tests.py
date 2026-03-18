from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status

from src.application.errors import InvariantViolationError, NotFoundError
from src.application.facade import (
    AssessmentContentFacade,
    CreateTestInput,
    TestQuestionData,
    TestQuestionOptionData,
    TestTextDistractorData,
)
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
    facade: FromDishka[AssessmentContentFacade],
) -> TestResponse:
    try:
        test = facade.create_test(
            payload=CreateTestInput(
                subject_code=body.subject_code,
                grade=body.grade,
                questions=[
                    TestQuestionData(
                        node_id=question.node_id,
                        text=question.text,
                        question_type=question.question_type,
                        answer_key=question.answer_key,
                        correct_option_id=question.correct_option_id,
                        options=[
                            TestQuestionOptionData(
                                option_id=option.option_id,
                                text=option.text,
                                position=option.position,
                                diagnostic_tag=option.diagnostic_tag,
                            )
                            for option in question.options
                        ],
                        text_distractors=[
                            TestTextDistractorData(
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
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

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
