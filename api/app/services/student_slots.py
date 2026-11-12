"""GET /student/slots: open slots for the student's badge, grouped by IST day (FR-S2)."""

from datetime import date, datetime, timedelta

from app.core.clock import utc_now
from app.core.errors import app_error
from app.core.rules import (
    AFTERNOON_ENDS_HOUR,
    BOOK_HORIZON,
    BOOK_MIN_LEAD,
    CHANGE_CUTOFF,
    IST,
    MORNING_ENDS_HOUR,
    RESCHEDULE_MAX,
)
from app.db.session import Conn
from app.deps.auth import Actor
from app.repositories import student_reads
from app.repositories.student_reads import JourneyView, OpenSlot
from app.schemas.student import CurrentSlot, Period, SlotDay, SlotsResponse, SlotTime


def period_of(moment: datetime) -> Period:
    hour = moment.astimezone(IST).hour
    if hour < MORNING_ENDS_HOUR:
        return "morning"
    return "afternoon" if hour < AFTERNOON_ENDS_HOUR else "evening"


def group_by_day(open_slots: list[OpenSlot], first: date, last: date) -> list[SlotDay]:
    """One entry per IST day; same start time across interviewers is shown once."""
    by_day: dict[date, dict[datetime, OpenSlot]] = {}
    for slot in open_slots:
        day = slot.start_at.astimezone(IST).date()
        by_day.setdefault(day, {}).setdefault(slot.start_at, slot)
    days: list[SlotDay] = []
    current = first
    while current <= last:
        unique = by_day.get(current, {})
        times = [
            SlotTime(
                slot_id=s.id, start_at=s.start_at, end_at=s.end_at, period=period_of(s.start_at)
            )
            for s in unique.values()
        ]
        days.append(SlotDay(date=current, open_count=len(times), times=times))
        current += timedelta(days=1)
    return days


def _bookable(journeys: list[JourneyView]) -> JourneyView:
    for journey in journeys:
        if journey.effective_state in ("eligible", "booked"):
            return journey
    raise app_error("not_eligible")


def _current(journey: JourneyView, now: datetime) -> CurrentSlot | None:
    if journey.effective_state != "booked" or journey.start_at is None:
        return None
    left = RESCHEDULE_MAX - (journey.reschedule_count or 0)
    return CurrentSlot(
        start_at=journey.start_at,
        reschedules_left=left,
        can_change=left > 0 and journey.start_at - now >= CHANGE_CUTOFF,
    )


async def list_slots(conn: Conn, actor: Actor) -> SlotsResponse:
    now = utc_now()
    journey = _bookable(await student_reads.journeys(conn, actor.user_id))
    window = (now + BOOK_MIN_LEAD, now + BOOK_HORIZON)
    found = await student_reads.open_slots(conn, journey.badge_id, window)
    first, last = now.astimezone(IST).date(), window[1].astimezone(IST).date()
    return SlotsResponse(
        days=group_by_day(found, first, last), current_booking=_current(journey, now)
    )
