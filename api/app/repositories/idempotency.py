"""SQL for Idempotency-Key replay (migration 005)."""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from app.db.session import Conn


async def find(
    conn: Conn, user_id: UUID, scope_key: tuple[str, str], since: datetime
) -> dict[str, Any] | None:
    raw = await conn.fetchval(
        """
        select response from idempotency_keys
        where user_id = $1 and scope = $2 and key = $3 and created_at >= $4
        """,
        user_id,
        scope_key[0],
        scope_key[1],
        since,
    )
    if raw is None:
        return None
    loaded: dict[str, Any] = json.loads(raw) if isinstance(raw, str) else dict(raw)
    return loaded


async def save(
    conn: Conn, user_id: UUID, scope_key: tuple[str, str], response: dict[str, Any]
) -> None:
    await conn.execute(
        """
        insert into idempotency_keys (user_id, scope, key, status_code, response)
        values ($1, $2, $3, 201, $4::jsonb)
        on conflict (user_id, scope, key) do update
          set response = excluded.response, created_at = now()
        """,
        user_id,
        scope_key[0],
        scope_key[1],
        json.dumps(response),
    )


async def purge_older_than(conn: Conn, before: datetime) -> None:
    await conn.execute("delete from idempotency_keys where created_at < $1", before)
