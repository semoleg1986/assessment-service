from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from src.application.facade import AssessmentImportFacade
from src.interface.http.v1.content_import import import_content_with_uow
from src.interface.http.v1.schemas import ContentImportRequest, ContentImportResponse

router = APIRouter(tags=["assessment"], route_class=DishkaRoute)


@router.post(
    "/admin/content/import",
    response_model=ContentImportResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def import_content(
    body: ContentImportRequest,
    facade: FromDishka[AssessmentImportFacade],
) -> ContentImportResponse:
    return import_content_with_uow(body=body, facade=facade)
