from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from src.application.errors import InvariantViolationError, NotFoundError
from src.application.facade import AssessmentContentFacade
from src.interface.http.policies import with_error_mapping
from src.interface.http.v1.mappers import (
    to_create_subject_input,
    to_create_topic_input,
    to_link_micro_skill_predecessors_input,
    to_upsert_micro_skill_input,
)
from src.interface.http.v1.admin._helpers import micro_skill_response
from src.interface.http.v1.schemas import (
    MicroSkillCreateRequest,
    MicroSkillLinkRequest,
    MicroSkillResponse,
    MicroSkillUpdateRequest,
    SubjectCreateRequest,
    SubjectResponse,
    TopicCreateRequest,
    TopicResponse,
)

router = APIRouter(tags=["assessment"], route_class=DishkaRoute)


def _micro_skill_blocks_count(node_id: str, *, facade: AssessmentContentFacade) -> int:
    return next(
        (
            item["blocks_count"]
            for item in facade.list_micro_skills()
            if item["node"].node_id == node_id
        ),
        0,
    )


@router.post(
    "/admin/subjects",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
@with_error_mapping((InvariantViolationError, 409))
def create_subject(
    body: SubjectCreateRequest,
    facade: FromDishka[AssessmentContentFacade],
) -> SubjectResponse:
    subject = facade.create_subject(payload=to_create_subject_input(body))
    return SubjectResponse(code=subject.code, name=subject.name)


@router.get("/admin/subjects", response_model=list[SubjectResponse])
def list_subjects(
    facade: FromDishka[AssessmentContentFacade],
) -> list[SubjectResponse]:
    subjects = facade.list_subjects()
    return [
        SubjectResponse(code=subject.code, name=subject.name) for subject in subjects
    ]


@router.post(
    "/admin/topics",
    response_model=TopicResponse,
    status_code=status.HTTP_201_CREATED,
)
@with_error_mapping((NotFoundError, 404), (InvariantViolationError, 409))
def create_topic(
    body: TopicCreateRequest,
    facade: FromDishka[AssessmentContentFacade],
) -> TopicResponse:
    topic = facade.create_topic(payload=to_create_topic_input(body))
    return TopicResponse(
        code=topic.code,
        subject_code=topic.subject_code,
        grade=topic.grade,
        name=topic.name,
    )


@router.get("/admin/topics", response_model=list[TopicResponse])
def list_topics(
    facade: FromDishka[AssessmentContentFacade],
) -> list[TopicResponse]:
    topics = facade.list_topics()
    return [
        TopicResponse(
            code=topic.code,
            subject_code=topic.subject_code,
            grade=topic.grade,
            name=topic.name,
        )
        for topic in topics
    ]


@router.post(
    "/admin/micro-skills",
    response_model=MicroSkillResponse,
    status_code=status.HTTP_201_CREATED,
)
@with_error_mapping((NotFoundError, 404), (InvariantViolationError, 409))
def create_micro_skill(
    body: MicroSkillCreateRequest,
    facade: FromDishka[AssessmentContentFacade],
) -> MicroSkillResponse:
    node = facade.create_micro_skill(payload=to_upsert_micro_skill_input(body=body))

    return micro_skill_response(node, blocks_count=0)


@router.put(
    "/admin/micro-skills/{node_id}",
    response_model=MicroSkillResponse,
)
@with_error_mapping((NotFoundError, 404), (InvariantViolationError, 409))
def update_micro_skill(
    node_id: str,
    body: MicroSkillUpdateRequest,
    facade: FromDishka[AssessmentContentFacade],
) -> MicroSkillResponse:
    node = facade.update_micro_skill(
        payload=to_upsert_micro_skill_input(node_id=node_id, body=body)
    )

    return micro_skill_response(
        node,
        blocks_count=_micro_skill_blocks_count(node.node_id, facade=facade),
    )


@router.delete(
    "/admin/micro-skills/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@with_error_mapping((NotFoundError, 404), (InvariantViolationError, 409))
def delete_micro_skill(
    node_id: str,
    facade: FromDishka[AssessmentContentFacade],
) -> None:
    facade.delete_micro_skill(node_id=node_id)


@router.post(
    "/admin/micro-skills/{node_id}/links",
    response_model=MicroSkillResponse,
)
@with_error_mapping((NotFoundError, 404), (InvariantViolationError, 409))
def link_micro_skill_predecessors(
    node_id: str,
    body: MicroSkillLinkRequest,
    facade: FromDishka[AssessmentContentFacade],
) -> MicroSkillResponse:
    node = facade.link_micro_skill_predecessors(
        payload=to_link_micro_skill_predecessors_input(node_id=node_id, body=body)
    )

    return micro_skill_response(
        node,
        blocks_count=_micro_skill_blocks_count(node.node_id, facade=facade),
    )


@router.get("/admin/micro-skills", response_model=list[MicroSkillResponse])
def list_micro_skills(
    facade: FromDishka[AssessmentContentFacade],
) -> list[MicroSkillResponse]:
    items = facade.list_micro_skills()
    return [
        micro_skill_response(item["node"], blocks_count=item["blocks_count"])
        for item in items
    ]
