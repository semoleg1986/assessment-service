from fastapi import APIRouter

from src.interface.http.v1.admin.assignments import router as assignments_router
from src.interface.http.v1.admin.content_crud import router as content_crud_router
from src.interface.http.v1.admin.imports import router as imports_router
from src.interface.http.v1.admin.maintenance import router as maintenance_router
from src.interface.http.v1.admin.results import router as results_router
from src.interface.http.v1.admin.tests import router as tests_router

router = APIRouter(tags=["assessment"])
router.include_router(imports_router)
router.include_router(maintenance_router)
router.include_router(content_crud_router)
router.include_router(tests_router)
router.include_router(assignments_router)
router.include_router(results_router)
