"""SQL for interview_journeys and journey_events."""

import json
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.core.rules import ActorRole
from app.db.session import Conn
from app.repositories.rows import JourneyRow

_SELECT = """
select j.id, j.student_id, j.badge_id, j.state, j.attempts_used, j.next_bookable_at,
       j.active_booking_id, j.priority, s.start_at as slot_start_at
from interview_journeys j
left join bookings b on b.id = j.active_booking_id
left join slots s on s.id = b.slot_id
"""


@dataclass(frozen=True)
class EventIn:
    journey_id: UUID
    from_state: str | None
    to_state: str
    actor_id: UUID | None
    actor_role: ActorRole
    reason: str
    meta: dict[str, Any] = field(default_factory=dict)


async def lock_for_student(conn: Conn, student_id: UUID) -> list[JourneyRow]:
    rows = await conn.fetch(
        _SELECT
        + """
        join badges bd on bd.id = j.badge_id
        where j.student_id = $1
        order by bd.level_order
        for update of j
        """,
        student_id,
    )
    return [JourneyRow.model_validate(dict(r)) for r in rows]


async def lock_by_id(conn: Conn, journey_id: UUID) -> JourneyRow | None:
    row = await conn.fetchrow(_SELECT + " where j.id = $1 for update of j", journey_id)
    return JourneyRow.model_validate(dict(row)) if row else None


async def save(conn: Conn, journey: JourneyRow) -> None:
    await conn.execute(
        """
        update interview_journeys
        set state = $2, attempts_used = $3, next_bookable_at = $4,
            active_booking_id = $5, priority = $6, updated_at = now()
        where id = $1
        """,
        journey.id,
        journey.state,
        journey.attempts_used,
        journey.next_bookable_at,
        journey.active_booking_id,
        journey.priority,
    )


async def insert_event(conn: Conn, event: EventIn) -> None:
    await conn.execute(
        """
        insert into journey_events
          (journey_id, from_state, to_state, actor_id, actor_role, reason, meta)
        values ($1, $2, $3, $4, $5, $6, $7::jsonb)
        """,
        event.journey_id,
        event.from_state,
        event.to_state,
        event.actor_id,
        event.actor_role,
        event.reason,
        json.dumps(event.meta, default=str),
    )
