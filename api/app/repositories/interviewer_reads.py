"""Read-only SQL for the interviewer schedule and interview detail panel."""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.core.rules import BookingStatus, OutcomeResult
from app.db.session import Conn


class ScheduleSlot(BaseModel):
    slot_id: UUID
    start_at: datetime
    end_at: datetime
    slot_status: str
    booking_id: UUID | None
    booking_status: BookingStatus | None
    student_name: str | None
    badge_level: str | None
    result: OutcomeResult | None


class PendingResult(BaseModel):
    booking_id: UUID
    student_name: str
    start_at: datetime
    end_at: datetime


class StudentFacts(BaseModel):
    campus: str
    batch: str
    badge_level: str


class ClearedSkill(BaseModel):
    name: str
    level: int


class Attempt(BaseModel):
    booking_id: UUID
    start_at: datetime
    result: OutcomeResult
    feedback_to_student: str
    recorded_at: datetime


class FullOutcome(BaseModel):
    result: OutcomeResult
    rubric: dict[str, int] | None
    feedback_to_student: str
    internal_notes: str
    retake_after: datetime | None
    recorded_at: datetime
    locked_at: datetime
    edited_at: datetime | None


async def schedule(
    conn: Conn, interviewer_id: UUID, day: tuple[datetime, datetime]
) -> list[ScheduleSlot]:
    rows = await conn.fetch(
        """
        select s.id as slot_id, s.start_at, s.end_at, s.status as slot_status,
               b.id as booking_id, b.status as booking_status, p.full_name as student_name,
               bd.level as badge_level, o.result
        from slots s
        left join lateral (
          select x.id, x.status, x.student_id, x.journey_id from bookings x
          where x.slot_id = s.id and x.status in ('confirmed', 'completed', 'no_show')
          order by x.booked_at desc limit 1
        ) b on true
        left join profiles p on p.id = b.student_id
        left join interview_journeys j on j.id = b.journey_id
        left join badges bd on bd.id = j.badge_id
        left join interview_outcomes o on o.booking_id = b.id
        where s.interviewer_id = $1 and s.start_at >= $2 and s.start_at < $3
          and not (
            s.status = 'cancelled' and b.id is null
            and exists (
              select 1 from availability_windows w
              where w.id = s.window_id and w.deleted_at is not null
            )
          )
        order by s.start_at
        """,
        interviewer_id,
        day[0],
        day[1],
    )
    return [ScheduleSlot.model_validate(dict(r)) for r in rows]


async def pending_results(conn: Conn, interviewer_id: UUID, now: datetime) -> list[PendingResult]:
    rows = await conn.fetch(
        """
        select b.id as booking_id, p.full_name as student_name, s.start_at, s.end_at
        from bookings b
        join slots s on s.id = b.slot_id
        join profiles p on p.id = b.student_id
        where s.interviewer_id = $1 and b.status = 'confirmed' and s.start_at <= $2
          and not exists (select 1 from interview_outcomes o where o.booking_id = b.id)
        order by s.start_at
        """,
        interviewer_id,
        now,
    )
    return [PendingResult.model_validate(dict(r)) for r in rows]


async def student_facts(conn: Conn, student_id: UUID, journey_id: UUID) -> StudentFacts:
    row = await conn.fetchrow(
        """
        select st.campus, st.batch, b.level as badge_level
        from students st, interview_journeys j join badges b on b.id = j.badge_id
        where st.id = $1 and j.id = $2
        """,
        student_id,
        journey_id,
    )
    if row is None:
        raise RuntimeError("student or journey missing for booking")
    return StudentFacts.model_validate(dict(row))


async def cleared_skills(conn: Conn, student_id: UUID) -> list[ClearedSkill]:
    rows = await conn.fetch(
        """
        select sk.name, max(l.level)::int as level
        from student_skill_levels l join skills sk on sk.id = l.skill_id
        where l.student_id = $1 and l.status = 'cleared'
        group by sk.name order by sk.name
        """,
        student_id,
    )
    return [ClearedSkill.model_validate(dict(r)) for r in rows]


async def earlier_attempts(conn: Conn, journey_id: UUID, booking_id: UUID) -> list[Attempt]:
    rows = await conn.fetch(
        """
        select o.booking_id, s.start_at, o.result, o.feedback_to_student, o.recorded_at
        from interview_outcomes o
        join bookings b on b.id = o.booking_id
        join slots s on s.id = b.slot_id
        where o.journey_id = $1 and o.booking_id <> $2
        order by s.start_at desc
        """,
        journey_id,
        booking_id,
    )
    return [Attempt.model_validate(dict(r)) for r in rows]


def _decode(raw: dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw.get("rubric"), str):
        raw["rubric"] = json.loads(raw["rubric"])
    return raw


async def full_outcome(conn: Conn, booking_id: UUID) -> FullOutcome | None:
    row = await conn.fetchrow(
        """
        select result, rubric, feedback_to_student, internal_notes, retake_after,
               recorded_at, locked_at, edited_at
        from interview_outcomes where booking_id = $1
        """,
        booking_id,
    )
    return FullOutcome.model_validate(_decode(dict(row))) if row else None


async def meeting_link(conn: Conn, booking_id: UUID) -> str | None:
    link = await conn.fetchval("select meeting_link from bookings where id = $1", booking_id)
    return str(link) if link is not None else None
