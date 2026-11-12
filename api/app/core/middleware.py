"""Request logging with request_id and user_id (PRD section 10 observability).
Logs every 4xx on booking routes so rule friction is visible."""

import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from http import HTTPStatus

from fastapi import Request, Response

logger = logging.getLogger("grit.request")


async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    extra = {
        "request_id": request_id,
        "user_id": str(getattr(request.state, "user_id", "")) or None,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "ms": round((time.perf_counter() - started) * 1000, 1),
    }
    is_client_error = response.status_code >= HTTPStatus.BAD_REQUEST
    is_booking_friction = is_client_error and "/bookings" in request.url.path
    logger.log(logging.WARNING if is_booking_friction else logging.INFO, "request", extra=extra)
    return response
