from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status

from src.application.content.commands.cleanup_fixtures import CleanupFixturesCommand
from src.application.content.handlers.cleanup_fixtures import handle_cleanup_fixtures
from src.application.ports.fixture_cleanup import (
    FixtureCleanupService,
    FixtureCleanupUnsupportedError,
)
from src.application.ports.unit_of_work import UnitOfWork
from src.interface.http.v1.admin._helpers import cleanup_counts_response
from src.interface.http.v1.schemas import (
    FixtureCleanupFiltersResponse,
    FixtureCleanupRequest,
    FixtureCleanupResponse,
)

router = APIRouter(tags=["assessment"], route_class=DishkaRoute)


@router.post(
    "/admin/fixtures/cleanup",
    response_model=FixtureCleanupResponse,
    status_code=status.HTTP_200_OK,
)
def cleanup_fixtures(
    body: FixtureCleanupRequest,
    uow: FromDishka[UnitOfWork],
    fixture_cleanup_service: FromDishka[FixtureCleanupService],
) -> FixtureCleanupResponse:
    try:
        result = handle_cleanup_fixtures(
            CleanupFixturesCommand(
                dry_run=body.dry_run,
                subject_code_patterns=tuple(body.subject_code_patterns),
                topic_code_patterns=tuple(body.topic_code_patterns),
                node_id_patterns=tuple(body.node_id_patterns),
            ),
            uow=uow,
            service=fixture_cleanup_service,
        )
    except FixtureCleanupUnsupportedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return FixtureCleanupResponse(
        status="planned" if result.dry_run else "completed",
        dry_run=result.dry_run,
        filters=FixtureCleanupFiltersResponse(
            subject_code_patterns=list(result.filters.subject_code_patterns),
            topic_code_patterns=list(result.filters.topic_code_patterns),
            node_id_patterns=list(result.filters.node_id_patterns),
        ),
        matched=cleanup_counts_response(
            subjects=result.matched.subjects,
            topics=result.matched.topics,
            micro_skills=result.matched.micro_skills,
            tests=result.matched.tests,
            questions=result.matched.questions,
            assignments=result.matched.assignments,
            attempts=result.matched.attempts,
            answers=result.matched.answers,
        ),
        deleted=cleanup_counts_response(
            subjects=result.deleted.subjects,
            topics=result.deleted.topics,
            micro_skills=result.deleted.micro_skills,
            tests=result.deleted.tests,
            questions=result.deleted.questions,
            assignments=result.deleted.assignments,
            attempts=result.deleted.attempts,
            answers=result.deleted.answers,
        ),
    )
