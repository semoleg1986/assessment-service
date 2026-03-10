from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dishka import make_async_container
from dishka.integrations.fastapi import FastapiProvider, setup_dishka
from fastapi import FastAPI

from src.interface.http.di import AppProvider
from src.interface.http.health import router as health_router
from src.interface.http.middleware import RequestIdLoggingMiddleware
from src.interface.http.v1.router import router as v1_router


def create_app() -> FastAPI:
    container = make_async_container(AppProvider(), FastapiProvider())

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        del app
        yield
        await container.close()

    app = FastAPI(title="assessment-service", version="0.1.0", lifespan=lifespan)
    app.add_middleware(RequestIdLoggingMiddleware)
    app.include_router(health_router)
    app.include_router(v1_router)
    setup_dishka(container=container, app=app)
    return app
