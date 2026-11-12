"""Interviewer schedule (FR-I1) and interview detail panel (FR-I2, FR-I4)."""

from datetime import date, datetime, time, timedelta
from uuid import UUID

from app.core.clock import utc_now
from app.core.errors import app_error
from app.core.rules import (
    IST,
    JOIN_OPENS_BEFORE,
    RESULT_OVERDUE_AFTER,
    BookingStatus,
    OutcomeResult,
)
from app.db.session import Conn
from app.deps.auth import Actor
from app.repositories import bookings, interviewer_reads
from app.repositories.interviewer_reads import ScheduleSlot
from app.schemas.interviewer import (
    AttemptItem,
    Chip,
    InterviewDetail,
    InterviewerOutcome,
    ResultToRecord,
    ScheduleItem,
    ScheduleResponse,
    SkillItem,
    StudentSummary,
)
from app.services.notify import badge_label

_RESULT_CHIPS: dict[OutcomeResult, Chip] = {
    "pass": "passed",
    "fail": "failed",
    "retake_later": "retake_later",
    "no_show": "no_show",
}
_SLOT_CHIPS: dict[str, Chip] = {"open": "open", "blocked": "blocked", "cancelled": "cancelled"}


def chip_for(
    slot: tuple[datetime, datetime, str],
    booking_status: BookingStatus | None,
    result: OutcomeResult | None,
    now: datetime,
) -> Chip:
    """Status chip for one slot. slot = (start_at, end_at, slot_status)."""
    start_at, end_at, slot_status = slot
    if result is not None:
        return _RESULT_CHIPS[result]
    if booking_status != "confirmed":
        return _SLOT_CHIPS.get(slot_status, "cancelled")
    if now < start_at:
        return "upcoming"
    if now < end_at:
        return "live_now"
    return "result_overdue" if now >= end_at + RESULT_OVERDUE_AFTER else "record_result"


def ist_day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=IST)
    return start, start + timedelta(days=1)


def _item(slot: ScheduleSlot, now: datetime) -> ScheduleItem:
    chip = chip_for(
        (slot.start_at, slot.end_at, slot.slot_status), slot.booking_status, slot.result, now
    )
    return ScheduleItem(
        slot_id=slot.slot_id,
        start_at=slot.start_at,
        end_at=slot.end_at,
        chip=chip,
        booking_id=slot.booking_id,
        student_name=slot.student_name,
        badge_name=badge_label(slot.badge_level) if slot.badge_level else None,
    )


async def get_schedule(conn: Conn, actor: Actor, day: date | None) -> ScheduleResponse:
    now = utc_now()
    target = day or now.astimezone(IST).date()
    slots = await interviewer_reads.schedule(conn, actor.user_id, ist_day_bounds(target))
    pending = await interviewer_reads.pending_results(conn, actor.user_id, now)
    return ScheduleResponse(
        date=target,
        items=[_item(s, now) for s in slots],
        to_record=[
            ResultToRecord(
                booking_id=p.booking_id,
                student_name=p.student_name,
                start_at=p.start_at,
                is_overdue=now >= p.end_at + RESULT_OVERDUE_AFTER,
            )
            for p in pending
            if now >= p.start_at
        ],
    )


async def _outcome(
    conn: Conn, actor: Actor, booking_id: UUID, now: datetime
) -> InterviewerOutcome | None:
    full = await interviewer_reads.full_outcome(conn, booking_id)
    if full is None:
        return None
    return InterviewerOutcome(
        result=full.result,
        rubric=full.rubric,
        feedback_to_student=full.feedback_to_student,
        internal_notes=full.internal_notes,
        retake_after=full.retake_after,
        recorded_at=full.recorded_at,
        editable_until=full.locked_at,
        can_edit=actor.role == "admin" or now < full.locked_at,
    )


async def get_interview(conn: Conn, actor: Actor, booking_id: UUID) -> InterviewDetail:
    now = utc_now()
    ctx = await bookings.get_context(conn, booking_id)
    if ctx is None:
        raise app_error("booking_not_found")
    if actor.role == "interviewer" and ctx.interviewer_id != actor.user_id:
        raise app_error("not_your_interview")
    facts = await interviewer_reads.student_facts(conn, ctx.student_id, ctx.journey_id)
    outcome = await _outcome(conn, actor, booking_id, now)
    is_confirmed = ctx.booking_status == "confirmed"
    attempts = await interviewer_reads.earlier_attempts(conn, ctx.journey_id, booking_id)
    return InterviewDetail(
        booking_id=booking_id,
        slot_id=ctx.slot_id,
        start_at=ctx.start_at,
        end_at=ctx.end_at,
        chip=chip_for(
            (ctx.start_at, ctx.end_at, "booked"),
            ctx.booking_status,
            outcome.result if outcome else None,
            now,
        ),
        badge_name=badge_label(facts.badge_level),
        meeting_link=await interviewer_reads.meeting_link(conn, booking_id),
        join_opens_at=ctx.start_at - JOIN_OPENS_BEFORE,
        is_join_open=ctx.start_at - JOIN_OPENS_BEFORE <= now < ctx.end_at,
        can_cancel=is_confirmed and now < ctx.start_at,
        can_record=is_confirmed and outcome is None and now >= ctx.start_at,
        student=StudentSummary(name=ctx.student_name, campus=facts.campus, batch=facts.batch),
        skills=[
            SkillItem(name=s.name, level=s.level)
            for s in await interviewer_reads.cleared_skills(conn, ctx.student_id)
        ],
        earlier_attempts=[AttemptItem.model_validate(a.model_dump()) for a in attempts],
        outcome=outcome,
    )
