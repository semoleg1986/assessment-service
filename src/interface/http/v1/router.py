from fastapi import APIRouter

from src.interface.http.v1.admin.router import router as admin_router
from src.interface.http.v1.content_import import import_content_with_uow
from src.interface.http.v1.user.router import router as user_router

router = APIRouter(prefix="/v1")
router.include_router(admin_router)
router.include_router(user_router)

# Backward compatibility for integration tests that import private symbol.
_import_content_with_uow = import_content_with_uow
