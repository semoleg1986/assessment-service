from __future__ import annotations

import logging
import time
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

# Use uvicorn logger so records go to container stdout
# with default uvicorn logging config.
logger = logging.getLogger("uvicorn.error")


class RequestIdLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid4())
        request.state.request_id = request_id
        started_at = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - started_at) * 1000
            logger.exception(
                ("request_failed method=%s path=%s duration_ms=%.2f request_id=%s"),
                request.method,
                request.url.path,
                duration_ms,
                request_id,
            )
            raise

        duration_ms = (time.perf_counter() - started_at) * 1000
        response.headers["x-request-id"] = request_id
        logger.info(
            (
                "request_completed method=%s path=%s status=%s "
                "duration_ms=%.2f request_id=%s"
            ),
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response
