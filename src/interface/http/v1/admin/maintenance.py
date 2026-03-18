from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from src.application.facade import AssessmentContentFacade
from src.application.ports.fixture_cleanup import FixtureCleanupUnsupportedError
from src.interface.http.policies import with_error_mapping
from src.interface.http.v1.admin._helpers import cleanup_counts_response
from src.interface.http.v1.mappers import to_cleanup_fixtures_input
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
@with_error_mapping((FixtureCleanupUnsupportedError, 501), (ValueError, 422))
def cleanup_fixtures(
    body: FixtureCleanupRequest,
    facade: FromDishka[AssessmentContentFacade],
) -> FixtureCleanupResponse:
    result = facade.cleanup_fixtures(payload=to_cleanup_fixtures_input(body))

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
