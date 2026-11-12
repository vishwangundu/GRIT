"""Idempotency-Key handling for POST booking and POST outcome (PRD section 10):
a repeated key within 10 minutes returns the first successful response."""

from collections.abc import Awaitable, Callable
from typing import TypeVar

from pydantic import BaseModel

from app.core.clock import utc_now
from app.core.rules import IDEMPOTENCY_TTL
from app.db.session import Conn
from app.deps.auth import Actor
from app.repositories import idempotency

ModelT = TypeVar("ModelT", bound=BaseModel)


async def run_once(
    conn: Conn,
    actor: Actor,
    scope_key: tuple[str, str | None],
    model: type[ModelT],
    produce: Callable[[], Awaitable[ModelT]],
) -> ModelT:
    scope, key = scope_key
    if not key:
        return await produce()
    since = utc_now() - IDEMPOTENCY_TTL
    cached = await idempotency.find(conn, actor.user_id, (scope, key), since)
    if cached is not None:
        return model.model_validate(cached)
    result = await produce()
    await idempotency.save(conn, actor.user_id, (scope, key), result.model_dump(mode="json"))
    return result
