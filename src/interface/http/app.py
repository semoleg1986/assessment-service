from fastapi import FastAPI

from src.interface.http.health import router as health_router
from src.interface.http.middleware import RequestIdLoggingMiddleware
from src.interface.http.v1.router import router as v1_router


def create_app() -> FastAPI:
    app = FastAPI(title="assessment-service", version="0.1.0")
    app.add_middleware(RequestIdLoggingMiddleware)
    app.include_router(health_router)
    app.include_router(v1_router)
    return app
