from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status

from src.application.errors import InvariantViolationError, NotFoundError
from src.application.facade import (
    AssessmentContentFacade,
    CreateSubjectInput,
    CreateTopicInput,
    LinkMicroSkillPredecessorsInput,
    UpsertMicroSkillInput,
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
def create_subject(
    body: SubjectCreateRequest,
    facade: FromDishka[AssessmentContentFacade],
) -> SubjectResponse:
    try:
        subject = facade.create_subject(
            payload=CreateSubjectInput(code=body.code, name=body.name)
        )
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
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
def create_topic(
    body: TopicCreateRequest,
    facade: FromDishka[AssessmentContentFacade],
) -> TopicResponse:
    try:
        topic = facade.create_topic(
            payload=CreateTopicInput(
                code=body.code,
                subject_code=body.subject_code,
                grade=body.grade,
                name=body.name,
            )
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
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
def create_micro_skill(
    body: MicroSkillCreateRequest,
    facade: FromDishka[AssessmentContentFacade],
) -> MicroSkillResponse:
    try:
        node = facade.create_micro_skill(
            payload=UpsertMicroSkillInput(
                node_id=body.node_id,
                subject_code=body.subject_code,
                topic_code=body.topic_code,
                grade=body.grade,
                section_code=body.section_code,
                section_name=body.section_name,
                micro_skill_name=body.micro_skill_name,
                predecessor_ids=body.predecessor_ids,
                criticality=body.criticality,
                source_ref=body.source_ref,
                description=body.description,
                status=body.status,
                external_ref=body.external_ref,
            )
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return micro_skill_response(node, blocks_count=0)


@router.put(
    "/admin/micro-skills/{node_id}",
    response_model=MicroSkillResponse,
)
def update_micro_skill(
    node_id: str,
    body: MicroSkillUpdateRequest,
    facade: FromDishka[AssessmentContentFacade],
) -> MicroSkillResponse:
    try:
        node = facade.update_micro_skill(
            payload=UpsertMicroSkillInput(
                node_id=node_id,
                subject_code=body.subject_code,
                topic_code=body.topic_code,
                grade=body.grade,
                section_code=body.section_code,
                section_name=body.section_name,
                micro_skill_name=body.micro_skill_name,
                predecessor_ids=body.predecessor_ids,
                criticality=body.criticality,
                source_ref=body.source_ref,
                description=body.description,
                status=body.status,
                external_ref=body.external_ref,
            )
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return micro_skill_response(
        node,
        blocks_count=_micro_skill_blocks_count(node.node_id, facade=facade),
    )


@router.delete(
    "/admin/micro-skills/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_micro_skill(
    node_id: str,
    facade: FromDishka[AssessmentContentFacade],
) -> None:
    try:
        facade.delete_micro_skill(node_id=node_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/admin/micro-skills/{node_id}/links",
    response_model=MicroSkillResponse,
)
def link_micro_skill_predecessors(
    node_id: str,
    body: MicroSkillLinkRequest,
    facade: FromDishka[AssessmentContentFacade],
) -> MicroSkillResponse:
    try:
        node = facade.link_micro_skill_predecessors(
            payload=LinkMicroSkillPredecessorsInput(
                node_id=node_id,
                predecessor_ids=body.predecessor_ids,
            )
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

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
