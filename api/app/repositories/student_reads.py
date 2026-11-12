"""Read-only SQL for the student dashboard and slot picker. Never selects internal_notes."""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.core.rules import JourneyState, OutcomeResult
from app.db.session import Conn


class JourneyView(BaseModel):
    id: UUID
    badge_id: int
    badge_level: str
    level_order: int
    track_id: int
    track_name: str
    state: JourneyState
    effective_state: JourneyState
    eligible_at: datetime | None
    attempts_used: int
    next_bookable_at: datetime | None
    priority: bool
    booking_id: UUID | None
    start_at: datetime | None
    end_at: datetime | None
    interviewer_id: UUID | None
    reschedule_count: int | None
    meeting_link: str | None


class SafeOutcome(BaseModel):
    result: OutcomeResult
    feedback_to_student: str
    rubric: dict[str, int] | None
    recorded_at: datetime
    retake_after: datetime | None


class LadderSkill(BaseModel):
    badge_id: int
    level: str
    level_order: int
    skill_name: str | None
    min_level: int | None
    cleared: bool


class EventView(BaseModel):
    from_state: str | None
    to_state: str
    reason: str | None
    created_at: datetime


class OpenSlot(BaseModel):
    id: UUID
    start_at: datetime
    end_at: datetime


async def journeys(conn: Conn, student_id: UUID) -> list[JourneyView]:
    rows = await conn.fetch(
        """
        select v.id, v.badge_id, b.level as badge_level, b.level_order, b.track_id,
               t.name as track_name, v.state, v.effective_state, v.eligible_at, v.attempts_used,
               v.next_bookable_at, v.priority, v.booking_id, v.start_at, v.end_at,
               v.interviewer_id, v.reschedule_count, v.meeting_link
        from v_journey_effective v
        join badges b on b.id = v.badge_id
        join tracks t on t.id = b.track_id
        where v.student_id = $1
        order by b.level_order
        """,
        student_id,
    )
    return [JourneyView.model_validate(dict(r)) for r in rows]


def _outcome(raw: dict[str, Any]) -> SafeOutcome:
    rubric = raw["rubric"]
    if isinstance(rubric, str):
        raw["rubric"] = json.loads(rubric)
    return SafeOutcome.model_validate(raw)


async def last_outcome(conn: Conn, journey_id: UUID) -> SafeOutcome | None:
    row = await conn.fetchrow(
        """
        select result, feedback_to_student, rubric, recorded_at, retake_after
        from interview_outcomes where journey_id = $1
        order by recorded_at desc limit 1
        """,
        journey_id,
    )
    return _outcome(dict(row)) if row else None


async def ladder(conn: Conn, track_id: int, student_id: UUID) -> list[LadderSkill]:
    rows = await conn.fetch(
        """
        select b.id as badge_id, b.level, b.level_order, sk.name as skill_name, r.min_level,
               coalesce(exists (
                 select 1 from student_skill_levels l
                 where l.student_id = $2 and l.skill_id = r.skill_id
                   and l.status = 'cleared' and l.level >= r.min_level), false) as cleared
        from badges b
        left join badge_skill_requirements r on r.badge_id = b.id
        left join skills sk on sk.id = r.skill_id
        where b.track_id = $1
        order by b.level_order, sk.name
        """,
        track_id,
        student_id,
    )
    return [LadderSkill.model_validate(dict(r)) for r in rows]


async def recent_events(conn: Conn, journey_id: UUID, limit: int) -> list[EventView]:
    rows = await conn.fetch(
        """
        select from_state, to_state, reason, created_at from journey_events
        where journey_id = $1 order by created_at desc, id desc limit $2
        """,
        journey_id,
        limit,
    )
    return [EventView.model_validate(dict(r)) for r in rows]


async def open_slots(
    conn: Conn, badge_id: int, window: tuple[datetime, datetime]
) -> list[OpenSlot]:
    rows = await conn.fetch(
        """
        select s.id, s.start_at, s.end_at from slots s
        join interviewer_badges ib on ib.interviewer_id = s.interviewer_id and ib.badge_id = $1
        join interviewers i on i.id = s.interviewer_id and i.active
        where s.status = 'open' and s.start_at >= $2 and s.start_at <= $3
        order by s.start_at, s.id
        """,
        badge_id,
        window[0],
        window[1],
    )
    return [OpenSlot.model_validate(dict(r)) for r in rows]
