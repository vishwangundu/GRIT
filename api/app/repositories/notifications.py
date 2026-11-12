"""SQL for notifications."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.db.session import Conn


@dataclass(frozen=True)
class NotificationIn:
    user_id: UUID
    template: str
    title: str
    body: str
    tone: str
    payload: dict[str, Any] = field(default_factory=dict)


async def insert(conn: Conn, note: NotificationIn) -> None:
    await conn.execute(
        """
        insert into notifications (user_id, template, title, body, tone, payload)
        values ($1, $2, $3, $4, $5, $6::jsonb)
        """,
        note.user_id,
        note.template,
        note.title,
        note.body,
        note.tone,
        json.dumps(note.payload, default=str),
    )


class NotificationView(BaseModel):
    id: UUID
    template: str
    title: str
    body: str
    tone: str
    created_at: datetime
    read_at: datetime | None


async def list_for_user(conn: Conn, user_id: UUID, limit: int = 100) -> list[NotificationView]:
    rows = await conn.fetch(
        """
        select id, template, title, body, tone, created_at, read_at from notifications
        where user_id = $1 and channel = 'in_app'
        order by created_at desc limit $2
        """,
        user_id,
        limit,
    )
    return [NotificationView.model_validate(dict(r)) for r in rows]


async def unread_count(conn: Conn, user_id: UUID) -> int:
    count = await conn.fetchval(
        "select count(*) from notifications where user_id = $1 and read_at is null", user_id
    )
    return int(count or 0)


async def mark_all_read(conn: Conn, user_id: UUID) -> int:
    result = await conn.execute(
        "update notifications set read_at = now() where user_id = $1 and read_at is null",
        user_id,
    )
    return int(result.split()[-1])


async def exists_for_booking(
    conn: Conn, template: str, booking_id: UUID, extra: dict[str, str]
) -> bool:
    """True when a notification of this template already exists for the booking + extra keys."""
    found = await conn.fetchval(
        """
        select 1 from notifications
        where template = $1 and payload->>'booking_id' = $2 and payload @> $3::jsonb
        limit 1
        """,
        template,
        str(booking_id),
        json.dumps(extra),
    )
    return found is not None
