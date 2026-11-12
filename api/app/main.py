"""FastAPI entry point: `uvicorn app.main:app`."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import scheduler
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import log_requests
from app.db.session import create_pool
from app.routers import admin, availability, internal, interviewer, meta, student

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    settings.require()
    app.state.pool = await create_pool(settings.database_url)
    job = scheduler.start(app.state.pool) if settings.scheduler_enabled else None
    try:
        yield
    finally:
        if job is not None:
            await scheduler.stop(job)
        await app.state.pool.close()


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="GRIT Interview Scheduling API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origin_list,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
    )
    app.middleware("http")(log_requests)
    register_error_handlers(app)
    routers = (meta, student, interviewer, availability, admin, internal)
    for router in (module.router for module in routers):
        app.include_router(router, prefix=API_PREFIX)
    return app


app = create_app()
