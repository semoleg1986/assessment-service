from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from src.application.ports.unit_of_work import UnitOfWork
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
    uow: FromDishka[UnitOfWork],
) -> ContentImportResponse:
    return import_content_with_uow(body=body, current_uow=uow)
