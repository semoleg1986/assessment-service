from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status

from src.application.content.commands.create_micro_skill import CreateMicroSkillCommand
from src.application.content.commands.create_subject import CreateSubjectCommand
from src.application.content.commands.create_topic import CreateTopicCommand
from src.application.content.commands.delete_micro_skill import DeleteMicroSkillCommand
from src.application.content.commands.link_micro_skill_predecessors import (
    LinkMicroSkillPredecessorsCommand,
)
from src.application.content.commands.update_micro_skill import UpdateMicroSkillCommand
from src.application.content.handlers.create_micro_skill import (
    handle_create_micro_skill,
)
from src.application.content.handlers.create_subject import handle_create_subject
from src.application.content.handlers.create_topic import handle_create_topic
from src.application.content.handlers.delete_micro_skill import (
    handle_delete_micro_skill,
)
from src.application.content.handlers.link_micro_skill_predecessors import (
    handle_link_micro_skill_predecessors,
)
from src.application.content.handlers.list_micro_skills import handle_list_micro_skills
from src.application.content.handlers.list_subjects import handle_list_subjects
from src.application.content.handlers.list_topics import handle_list_topics
from src.application.content.handlers.update_micro_skill import (
    handle_update_micro_skill,
)
from src.application.content.queries.list_micro_skills import ListMicroSkillsQuery
from src.application.content.queries.list_subjects import ListSubjectsQuery
from src.application.content.queries.list_topics import ListTopicsQuery
from src.application.errors import InvariantViolationError, NotFoundError
from src.application.ports.unit_of_work import UnitOfWork
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


def _micro_skill_blocks_count(node_id: str, *, uow: UnitOfWork) -> int:
    return next(
        (
            item["blocks_count"]
            for item in handle_list_micro_skills(ListMicroSkillsQuery(), uow=uow)
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
    uow: FromDishka[UnitOfWork],
) -> SubjectResponse:
    try:
        subject = handle_create_subject(
            CreateSubjectCommand(code=body.code, name=body.name),
            uow=uow,
        )
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return SubjectResponse(code=subject.code, name=subject.name)


@router.get("/admin/subjects", response_model=list[SubjectResponse])
def list_subjects(
    uow: FromDishka[UnitOfWork],
) -> list[SubjectResponse]:
    subjects = handle_list_subjects(ListSubjectsQuery(), uow=uow)
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
    uow: FromDishka[UnitOfWork],
) -> TopicResponse:
    try:
        topic = handle_create_topic(
            CreateTopicCommand(
                code=body.code,
                subject_code=body.subject_code,
                grade=body.grade,
                name=body.name,
            ),
            uow=uow,
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
    uow: FromDishka[UnitOfWork],
) -> list[TopicResponse]:
    topics = handle_list_topics(ListTopicsQuery(), uow=uow)
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
    uow: FromDishka[UnitOfWork],
) -> MicroSkillResponse:
    try:
        node = handle_create_micro_skill(
            CreateMicroSkillCommand(
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
            ),
            uow=uow,
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
    uow: FromDishka[UnitOfWork],
) -> MicroSkillResponse:
    try:
        node = handle_update_micro_skill(
            UpdateMicroSkillCommand(
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
            ),
            uow=uow,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return micro_skill_response(
        node,
        blocks_count=_micro_skill_blocks_count(node.node_id, uow=uow),
    )


@router.delete(
    "/admin/micro-skills/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_micro_skill(
    node_id: str,
    uow: FromDishka[UnitOfWork],
) -> None:
    try:
        handle_delete_micro_skill(
            DeleteMicroSkillCommand(node_id=node_id),
            uow=uow,
        )
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
    uow: FromDishka[UnitOfWork],
) -> MicroSkillResponse:
    try:
        node = handle_link_micro_skill_predecessors(
            LinkMicroSkillPredecessorsCommand(
                node_id=node_id,
                predecessor_ids=body.predecessor_ids,
            ),
            uow=uow,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvariantViolationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return micro_skill_response(
        node,
        blocks_count=_micro_skill_blocks_count(node.node_id, uow=uow),
    )


@router.get("/admin/micro-skills", response_model=list[MicroSkillResponse])
def list_micro_skills(
    uow: FromDishka[UnitOfWork],
) -> list[MicroSkillResponse]:
    items = handle_list_micro_skills(ListMicroSkillsQuery(), uow=uow)
    return [
        micro_skill_response(item["node"], blocks_count=item["blocks_count"])
        for item in items
    ]
