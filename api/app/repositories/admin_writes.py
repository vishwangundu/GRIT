"""SQL for admin actions: nudges, flags, award status, reassignment."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.db.session import Conn


class NudgeCandidate(BaseModel):
    journey_id: UUID
    student_id: UUID
    eligible_at: datetime | None
    last_nudged_at: datetime | None


class FlagRow(BaseModel):
    id: UUID
    badge_award_id: UUID
    student_id: UUID
    status: str


class LiveAward(BaseModel):
    id: UUID
    badge_id: int
    status: str
    miles_awarded: int


async def nudge_candidates_by_ids(
    conn: Conn, now: datetime, student_ids: list[UUID]
) -> list[NudgeCandidate]:
    rows = await conn.fetch(
        """
        select j.id as journey_id, j.student_id, j.eligible_at, j.last_nudged_at
        from interview_journeys j
        where (j.state = 'eligible'
               or (j.state in ('retake_later', 'failed') and j.next_bookable_at <= $1))
          and j.student_id = any($2::uuid[])
        order by j.eligible_at
        for update
        """,
        now,
        student_ids,
    )
    return [NudgeCandidate.model_validate(dict(r)) for r in rows]


async def nudge_candidates_waiting(
    conn: Conn, now: datetime, eligible_before: datetime
) -> list[NudgeCandidate]:
    rows = await conn.fetch(
        """
        select j.id as journey_id, j.student_id, j.eligible_at, j.last_nudged_at
        from interview_journeys j
        where (j.state = 'eligible'
               or (j.state in ('retake_later', 'failed') and j.next_bookable_at <= $1))
          and j.eligible_at <= $2
        order by j.eligible_at
        for update
        """,
        now,
        eligible_before,
    )
    return [NudgeCandidate.model_validate(dict(r)) for r in rows]


async def mark_nudged(conn: Conn, journey_id: UUID, at: datetime) -> None:
    await conn.execute(
        "update interview_journeys set last_nudged_at = $2 where id = $1", journey_id, at
    )


async def journey_id_for(conn: Conn, student_id: UUID, badge_id: int) -> UUID | None:
    found = await conn.fetchval(
        "select id from interview_journeys where student_id = $1 and badge_id = $2",
        student_id,
        badge_id,
    )
    return UUID(str(found)) if found else None


async def live_award(conn: Conn, student_id: UUID, badge_id: int) -> LiveAward | None:
    row = await conn.fetchrow(
        """
        select id, badge_id, status, miles_awarded from badge_awards
        where student_id = $1 and badge_id = $2 and status <> 'nullified'
        for update
        """,
        student_id,
        badge_id,
    )
    return LiveAward.model_validate(dict(row)) if row else None


async def award_by_id(conn: Conn, award_id: UUID) -> LiveAward | None:
    row = await conn.fetchrow(
        "select id, badge_id, status, miles_awarded from badge_awards where id = $1 for update",
        award_id,
    )
    return LiveAward.model_validate(dict(row)) if row else None


async def set_award_status(
    conn: Conn, award_id: UUID, status: str, nullified: tuple[datetime, str] | None = None
) -> None:
    await conn.execute(
        """
        update badge_awards set status = $2, nullified_at = $3, reason = coalesce($4, reason)
        where id = $1
        """,
        award_id,
        status,
        nullified[0] if nullified else None,
        nullified[1] if nullified else None,
    )


async def insert_flag(
    conn: Conn, award_id: UUID, student_id: UUID, raised_by: UUID, source: tuple[str, str | None]
) -> UUID:
    flag_id = await conn.fetchval(
        """
        insert into malpractice_flags (badge_award_id, student_id, raised_by, source, evidence_url)
        values ($1, $2, $3, $4, $5) returning id
        """,
        award_id,
        student_id,
        raised_by,
        source[0],
        source[1],
    )
    return UUID(str(flag_id))


async def lock_flag(conn: Conn, flag_id: UUID) -> FlagRow | None:
    row = await conn.fetchrow(
        """
        select id, badge_award_id, student_id, status from malpractice_flags
        where id = $1 for update
        """,
        flag_id,
    )
    return FlagRow.model_validate(dict(row)) if row else None


async def decide_flag(
    conn: Conn, flag_id: UUID, decision: tuple[str, UUID, str], at: datetime
) -> None:
    status, decided_by, note = decision
    await conn.execute(
        """
        update malpractice_flags
        set status = $2, decided_by = $3, decision_note = $4, decided_at = $5
        where id = $1
        """,
        flag_id,
        status,
        decided_by,
        note,
        at,
    )


async def free_slot_at(conn: Conn, interviewer_id: UUID, start_at: datetime) -> UUID | None:
    found = await conn.fetchval(
        """
        select id from slots where interviewer_id = $1 and start_at = $2 and status = 'open'
        for update
        """,
        interviewer_id,
        start_at,
    )
    return UUID(str(found)) if found else None


async def move_booking(conn: Conn, booking_id: UUID, slot_id: UUID, link: str | None) -> None:
    await conn.execute(
        "update bookings set slot_id = $2, meeting_link = $3 where id = $1",
        booking_id,
        slot_id,
        link,
    )


async def reassign_options(conn: Conn, booking_id: UUID) -> list[tuple[UUID, str]]:
    rows = await conn.fetch(
        """
        select i.id, p.full_name
        from bookings b
        join slots cur on cur.id = b.slot_id
        join interview_journeys j on j.id = b.journey_id
        join slots s on s.start_at = cur.start_at and s.status = 'open'
                     and s.interviewer_id <> cur.interviewer_id
        join interviewers i on i.id = s.interviewer_id and i.active
        join interviewer_badges ib on ib.interviewer_id = i.id and ib.badge_id = j.badge_id
        join profiles p on p.id = i.id
        where b.id = $1
        order by p.full_name
        """,
        booking_id,
    )
    return [(UUID(str(r["id"])), str(r["full_name"])) for r in rows]


async def admin_ids(conn: Conn) -> list[UUID]:
    rows = await conn.fetch("select id from profiles where role = 'admin'")
    return [UUID(str(r["id"])) for r in rows]
