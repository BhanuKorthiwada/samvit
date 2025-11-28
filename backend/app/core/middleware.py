"""Request middleware for tracing and logging."""

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID for tracing."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        # Get tenant ID from request state (set by TenantMiddleware via domain lookup)
        tenant_id = getattr(request.state, "tenant_id", None) or "-"

        # Add to logging context
        logger_adapter = logger
        extra = {"request_id": request_id, "tenant_id": tenant_id}

        # Log request start
        start_time = time.perf_counter()
        logger_adapter.info(
            f"Request started: {request.method} {request.url.path}",
            extra=extra,
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log request completion
        logger_adapter.info(
            f"Request completed: {request.method} {request.url.path} "
            f"- Status: {response.status_code} - Duration: {duration_ms:.2f}ms",
            extra=extra,
        )

        # Add headers to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response
