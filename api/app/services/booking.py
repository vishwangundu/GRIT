"""Book, reschedule and cancel interviews (PRD S1-S4, I4). Race-safe by construction:
the journey row is locked FOR UPDATE and the slot is claimed with a conditional UPDATE."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.clock import utc_now
from app.core.errors import app_error
from app.core.rules import (
    BOOK_HORIZON,
    BOOK_MIN_LEAD,
    CHANGE_CUTOFF,
    RESCHEDULE_MAX,
    JourneyState,
)
from app.db.session import Conn
from app.deps.auth import Actor
from app.repositories import bookings, journeys, slots
from app.repositories.bookings import BookingIn, Cancellation
from app.repositories.rows import BookingRow, JourneyRow, SlotRow
from app.services import notify
from app.services.journey import Audit, effective_state, persist_derived, transition


@dataclass(frozen=True)
class BookingResult:
    booking_id: UUID
    state: JourneyState
    start_at: datetime
    end_at: datetime
    interviewer_name: str
    reschedules_left: int
    meeting_link: str | None


async def _active_journey(conn: Conn, student_id: UUID, now: datetime) -> JourneyRow:
    """Lock the student's journeys and return the one that can book or reschedule."""
    for journey in await journeys.lock_for_student(conn, student_id):
        if effective_state(journey, now) in ("eligible", "booked"):
            return await persist_derived(conn, journey, now)
    raise app_error("not_eligible")


async def _bookable_slot(conn: Conn, slot_id: UUID, badge_id: int, now: datetime) -> SlotRow:
    slot = await slots.get(conn, slot_id)
    if slot is None:
        raise app_error("slot_not_found")
    if slot.start_at < now + BOOK_MIN_LEAD:
        raise app_error("too_soon")
    if slot.start_at > now + BOOK_HORIZON:
        raise app_error("too_far")
    if not await slots.interviewer_has_badge(conn, slot.interviewer_id, badge_id):
        raise app_error("badge_mismatch")
    return slot


async def _current_booking(conn: Conn, journey: JourneyRow) -> BookingRow:
    if journey.active_booking_id is None:
        raise app_error("no_booking")
    booking = await bookings.get(conn, journey.active_booking_id)
    if booking is None or booking.status != "confirmed":
        raise app_error("no_booking")
    return booking


def _check_change_window(journey: JourneyRow, now: datetime) -> None:
    if journey.slot_start_at is None or journey.slot_start_at - now < CHANGE_CUTOFF:
        raise app_error("change_window_closed")


async def _reschedulable_booking(conn: Conn, journey: JourneyRow, now: datetime) -> BookingRow:
    current = await _current_booking(conn, journey)
    if current.reschedule_count >= RESCHEDULE_MAX:
        raise app_error("reschedule_limit")
    _check_change_window(journey, now)
    return current


async def _release(conn: Conn, current: BookingRow) -> int:
    """Mark the old booking rescheduled, reopen its slot, return the new reschedule_count."""
    await bookings.set_status(conn, current.id, "rescheduled")
    await slots.set_status(conn, current.slot_id, "open")
    return current.reschedule_count + 1


async def book_slot(conn: Conn, actor: Actor, slot_id: UUID) -> BookingResult:
    """POST /student/bookings: book a first slot, or reschedule when already booked."""
    now = utc_now()
    async with conn.transaction():
        journey = await _active_journey(conn, actor.user_id, now)
        is_reschedule = journey.state == "booked"
        current = await _reschedulable_booking(conn, journey, now) if is_reschedule else None
        slot = await _bookable_slot(conn, slot_id, journey.badge_id, now)
        if not await slots.claim_open(conn, slot.id):
            raise app_error("slot_taken")
        count = await _release(conn, current) if current else 0
        name, link = await slots.interviewer_details(conn, slot.interviewer_id)
        booking_id = await bookings.insert(
            conn, BookingIn(journey.id, slot.id, actor.user_id, count, link)
        )
        after = journey.model_copy(
            update={"state": "booked", "active_booking_id": booking_id, "priority": False}
        )
        reason = "student_rescheduled" if is_reschedule else "student_booked"
        await transition(conn, journey, after, Audit(actor, reason, {"slot_id": slot.id}))
        await _notify_booked(conn, journey, slot)
    return BookingResult(
        booking_id=booking_id,
        state="booked",
        start_at=slot.start_at,
        end_at=slot.end_at,
        interviewer_name=name,
        reschedules_left=RESCHEDULE_MAX - count,
        meeting_link=link,
    )


async def _notify_booked(conn: Conn, journey: JourneyRow, slot: SlotRow) -> None:
    values = await notify.badge_vars(conn, journey.badge_id, journey.student_id)
    values |= {
        "date": notify.ist_date(slot.start_at),
        "start": notify.ist_time(slot.start_at),
        "end": notify.ist_time(slot.end_at),
    }
    await notify.send(conn, journey.student_id, "booked", values, {"slot_id": str(slot.id)})


async def cancel_by_student(conn: Conn, actor: Actor) -> JourneyState:
    """DELETE /student/bookings/current: allowed until 12 h before; no attempt used."""
    now = utc_now()
    async with conn.transaction():
        booked = [
            j for j in await journeys.lock_for_student(conn, actor.user_id) if j.state == "booked"
        ]
        if not booked:
            raise app_error("no_booking")
        journey = booked[0]
        current = await _current_booking(conn, journey)
        _check_change_window(journey, now)
        await bookings.cancel(
            conn, current.id, "cancelled_by_student", Cancellation(actor.user_id, now, None)
        )
        await slots.set_status(conn, current.slot_id, "open")
        after = journey.model_copy(update={"state": "eligible", "active_booking_id": None})
        await transition(conn, journey, after, Audit(actor, "student_cancelled"))
    return "eligible"


async def cancel_by_interviewer(conn: Conn, actor: Actor, slot_id: UUID, reason: str) -> bool:
    """POST /interviewer/slots/{slot_id}/cancel: student goes back to eligible with priority."""
    now = utc_now()
    async with conn.transaction():
        slot = await slots.get(conn, slot_id)
        if slot is None:
            raise app_error("slot_not_found")
        if actor.role == "interviewer" and slot.interviewer_id != actor.user_id:
            raise app_error("not_your_interview")
        booking = await bookings.confirmed_for_slot(conn, slot_id)
        if booking is None:
            raise app_error("no_booking")
        if slot.start_at <= now:
            raise app_error("interview_started")
        journey = await journeys.lock_by_id(conn, booking.journey_id)
        if journey is None or journey.active_booking_id != booking.id:
            raise app_error("booking_not_active")
        await bookings.cancel(
            conn, booking.id, "cancelled_by_interviewer", Cancellation(actor.user_id, now, reason)
        )
        await slots.set_status(conn, slot_id, "cancelled")
        after = journey.model_copy(
            update={"state": "eligible", "active_booking_id": None, "priority": True}
        )
        audit = Audit(actor, "interviewer_cancelled", {"cancel_reason": reason})
        await transition(conn, journey, after, audit)
        values = {"date": notify.ist_date(slot.start_at), "reason": reason}
        await notify.send(conn, journey.student_id, "iv_cancelled", values)
    return True
