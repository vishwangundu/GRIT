"""POST /internal/eligibility/recompute: keep journeys in step with cleared skills.

not_eligible -> eligible when every required skill is cleared; eligible or booked ->
not_eligible when a skill is revoked (the booking is cancelled by the system, slot reopens).
"""

from datetime import datetime
from uuid import UUID

from app.core.clock import utc_now
from app.core.errors import app_error
from app.db.session import Conn
from app.repositories import bookings, eligibility, journeys, slots
from app.repositories.bookings import Cancellation
from app.repositories.eligibility import BadgeProgress
from app.repositories.rows import JourneyRow
from app.schemas.internal import JourneyStateOut, RecomputeResponse
from app.services import notify
from app.services.journey import Audit, effective_state, transition

_SYSTEM = Audit(actor=None, reason="eligibility_recompute")


async def _make_eligible(
    conn: Conn, journey: JourneyRow, required: int, now: datetime
) -> JourneyRow:
    after = await transition(
        conn, journey, journey.model_copy(update={"state": "eligible"}), _SYSTEM
    )
    await eligibility.set_eligible_at(conn, journey.id, now)
    values = await notify.badge_vars(conn, journey.badge_id, journey.student_id)
    values["skill_count"] = str(required)
    await notify.send(conn, journey.student_id, "eligible", values)
    return after


async def _revoke(conn: Conn, journey: JourneyRow, now: datetime) -> JourneyRow:
    if journey.state == "booked" and effective_state(journey, now) == "booked":
        booking_id = journey.active_booking_id
        booking = await bookings.get(conn, booking_id) if booking_id else None
        if booking is not None:
            cancel = Cancellation(by=journey.student_id, at=now, reason="skill_revoked")
            await bookings.cancel(conn, booking.id, "cancelled_by_system", cancel)
            await slots.set_status(conn, booking.slot_id, "open")
    elif journey.state != "eligible":
        return journey
    after = journey.model_copy(update={"state": "not_eligible", "active_booking_id": None})
    return await transition(conn, journey, after, _SYSTEM)


async def _apply(conn: Conn, student_id: UUID, badge: BadgeProgress, now: datetime) -> JourneyRow:
    journey_id = await eligibility.ensure_journey(conn, student_id, badge.id)
    journey = await journeys.lock_by_id(conn, journey_id)
    if journey is None:
        raise app_error("student_not_found")
    is_met = badge.required > 0 and badge.met == badge.required
    if is_met and journey.state == "not_eligible":
        return await _make_eligible(conn, journey, badge.required, now)
    if not is_met:
        return await _revoke(conn, journey, now)
    return journey


async def recompute(conn: Conn, student_id: UUID) -> RecomputeResponse:
    now = utc_now()
    async with conn.transaction():
        if not await eligibility.student_exists(conn, student_id):
            raise app_error("student_not_found")
        changed: list[JourneyStateOut] = []
        for badge in await eligibility.badge_progress(conn, student_id):
            if badge.level_order == 1 or badge.prev_passed:
                journey = await _apply(conn, student_id, badge, now)
                changed.append(JourneyStateOut(badge_id=badge.id, state=journey.state))
    return RecomputeResponse(student_id=student_id, journeys=changed)
