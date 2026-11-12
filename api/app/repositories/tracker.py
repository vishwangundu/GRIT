"""Read-only SQL for the admin tracker (FR-A1 to FR-A5). badge_id None means all badges."""

from datetime import datetime, timedelta
from uuid import UUID

from pydantic import BaseModel

from app.core.rules import JourneyState, OutcomeResult
from app.db.session import Conn


class Tiles(BaseModel):
    not_booked: int
    booked: int
    awaiting: int
    awaiting_overdue: int
    results: int


class NotBookedRaw(BaseModel):
    student_id: UUID
    name: str
    campus: str
    effective_state: JourneyState
    priority: bool
    eligible_at: datetime | None
    next_bookable_at: datetime | None
    last_nudged_at: datetime | None
    has_outcome: bool


class BookedRaw(BaseModel):
    student_id: UUID
    booking_id: UUID
    slot_id: UUID
    name: str
    campus: str
    start_at: datetime
    interviewer_name: str
    booked_at: datetime
    reschedule_count: int


class AwaitingRaw(BaseModel):
    student_id: UUID
    booking_id: UUID
    name: str
    campus: str
    start_at: datetime
    end_at: datetime
    interviewer_name: str


class ResultRaw(BaseModel):
    student_id: UUID
    badge_id: int
    booking_id: UUID
    name: str
    campus: str
    result: OutcomeResult
    recorded_at: datetime
    interviewer_name: str
    award_status: str | None
    journey_state: JourneyState
    open_flag_id: UUID | None


class BadgeOption(BaseModel):
    id: int
    level: str
    track_name: str


async def tiles(conn: Conn, badge_id: int | None, now: datetime, overdue: timedelta) -> Tiles:
    row = await conn.fetchrow(
        """
        select
          count(*) filter (where effective_state in ('eligible', 'retake_later', 'failed'))
            as not_booked,
          count(*) filter (where effective_state = 'booked') as booked,
          count(*) filter (where effective_state = 'awaiting_result') as awaiting,
          count(*) filter (where effective_state = 'awaiting_result' and $2 >= end_at + $3)
            as awaiting_overdue,
          (select count(*) from interview_outcomes o join interview_journeys j
             on j.id = o.journey_id where $1::int is null or j.badge_id = $1) as results
        from v_journey_effective
        where $1::int is null or badge_id = $1
        """,
        badge_id,
        now,
        overdue,
    )
    return Tiles.model_validate(dict(row) if row else {})


async def not_booked(conn: Conn, badge_id: int | None) -> list[NotBookedRaw]:
    rows = await conn.fetch(
        """
        select v.student_id, p.full_name as name, st.campus, v.effective_state, v.priority,
               v.eligible_at, v.next_bookable_at, v.last_nudged_at,
               exists (select 1 from interview_outcomes o where o.journey_id = v.id)
                 as has_outcome
        from v_journey_effective v
        join profiles p on p.id = v.student_id
        join students st on st.id = v.student_id
        where v.effective_state in ('eligible', 'retake_later', 'failed')
          and ($1::int is null or v.badge_id = $1)
        order by v.eligible_at asc nulls last, p.full_name
        """,
        badge_id,
    )
    return [NotBookedRaw.model_validate(dict(r)) for r in rows]


async def booked(conn: Conn, badge_id: int | None, state: str) -> list[BookedRaw]:
    rows = await conn.fetch(
        """
        select v.student_id, v.booking_id, v.slot_id, p.full_name as name, st.campus,
               v.start_at, ip.full_name as interviewer_name, b.booked_at, v.reschedule_count
        from v_journey_effective v
        join profiles p on p.id = v.student_id
        join students st on st.id = v.student_id
        join bookings b on b.id = v.booking_id
        join profiles ip on ip.id = v.interviewer_id
        where v.effective_state = $2 and ($1::int is null or v.badge_id = $1)
        order by v.start_at
        """,
        badge_id,
        state,
    )
    return [BookedRaw.model_validate(dict(r)) for r in rows]


async def awaiting(conn: Conn, badge_id: int | None) -> list[AwaitingRaw]:
    rows = await conn.fetch(
        """
        select v.student_id, v.booking_id, p.full_name as name, st.campus, v.start_at,
               v.end_at, ip.full_name as interviewer_name
        from v_journey_effective v
        join profiles p on p.id = v.student_id
        join students st on st.id = v.student_id
        join profiles ip on ip.id = v.interviewer_id
        where v.effective_state = 'awaiting_result' and ($1::int is null or v.badge_id = $1)
        order by v.end_at
        """,
        badge_id,
    )
    return [AwaitingRaw.model_validate(dict(r)) for r in rows]


async def results(conn: Conn, badge_id: int | None) -> list[ResultRaw]:
    rows = await conn.fetch(
        """
        select j.student_id, j.badge_id, o.booking_id, p.full_name as name, st.campus,
               o.result, o.recorded_at, ip.full_name as interviewer_name,
               a.status as award_status, j.state as journey_state, f.id as open_flag_id
        from interview_outcomes o
        join interview_journeys j on j.id = o.journey_id
        join profiles p on p.id = j.student_id
        join students st on st.id = j.student_id
        join profiles ip on ip.id = o.interviewer_id
        left join lateral (
          select x.id, x.status from badge_awards x where x.outcome_id = o.id
          order by x.awarded_at desc limit 1
        ) a on true
        left join lateral (
          select y.id from malpractice_flags y
          where y.badge_award_id = a.id and y.status = 'open' limit 1
        ) f on true
        where $1::int is null or j.badge_id = $1
        order by o.recorded_at desc
        """,
        badge_id,
    )
    return [ResultRaw.model_validate(dict(r)) for r in rows]


async def badge_options(conn: Conn) -> list[BadgeOption]:
    rows = await conn.fetch(
        """
        select b.id, b.level, t.name as track_name
        from badges b join tracks t on t.id = b.track_id
        order by t.name, b.level_order
        """
    )
    return [BadgeOption.model_validate(dict(r)) for r in rows]
