"""Admin nudges, interviewer reminders and booking reassignment (A2, FR-A4, FR-A6)."""

from datetime import timedelta
from uuid import UUID

from app.core.clock import utc_now
from app.core.errors import app_error
from app.core.rules import NUDGE_COOLDOWN
from app.db.session import Conn
from app.deps.auth import Actor
from app.repositories import admin_writes, bookings, journeys, outcomes, slots
from app.repositories.admin_writes import NudgeCandidate
from app.schemas.admin import (
    NudgeRequest,
    NudgeResponse,
    ReassignOption,
    ReassignOptions,
    ReassignResponse,
)
from app.services import notify
from app.services.journey import Audit, transition


async def _candidates(conn: Conn, body: NudgeRequest) -> list[NudgeCandidate]:
    now = utc_now()
    if body.student_ids:
        return await admin_writes.nudge_candidates_by_ids(conn, now, body.student_ids)
    if body.min_days_waiting is None:
        raise app_error("nudge_target_required")
    before = now - timedelta(days=body.min_days_waiting)
    return await admin_writes.nudge_candidates_waiting(conn, now, before)


async def send_nudges(conn: Conn, body: NudgeRequest) -> NudgeResponse:
    """At most one nudge per student per 24 h."""
    now = utc_now()
    sent = skipped = 0
    async with conn.transaction():
        for candidate in await _candidates(conn, body):
            last = candidate.last_nudged_at
            if last is not None and now - last < NUDGE_COOLDOWN:
                skipped += 1
                continue
            days = (now - candidate.eligible_at).days if candidate.eligible_at else 0
            await admin_writes.mark_nudged(conn, candidate.journey_id, now)
            await notify.send(conn, candidate.student_id, "nudge", {"days": str(days)})
            sent += 1
    return NudgeResponse(sent=sent, skipped_recent=skipped)


async def remind_interviewer(conn: Conn, booking_id: UUID) -> bool:
    ctx = await bookings.get_context(conn, booking_id)
    if ctx is None:
        raise app_error("booking_not_found")
    if ctx.booking_status != "confirmed" or await outcomes.get_by_booking(conn, booking_id):
        raise app_error("booking_not_active")
    values = {
        "student": ctx.student_name,
        "date": notify.ist_date(ctx.start_at),
        "start": notify.ist_time(ctx.start_at),
    }
    payload = {"booking_id": str(booking_id), "stage": "manual"}
    await notify.send(conn, ctx.interviewer_id, "iv_result_reminder", values, payload)
    return True


async def reassign_options(conn: Conn, booking_id: UUID) -> ReassignOptions:
    found = await admin_writes.reassign_options(conn, booking_id)
    return ReassignOptions(
        options=[ReassignOption(interviewer_id=i, name=name) for i, name in found]
    )


async def reassign(
    conn: Conn, actor: Actor, booking_id: UUID, interviewer_id: UUID
) -> ReassignResponse:
    """Move a booking to another cleared interviewer's free slot at the same time."""
    async with conn.transaction():
        ctx = await bookings.get_context(conn, booking_id)
        if ctx is None:
            raise app_error("booking_not_found")
        journey = await journeys.lock_by_id(conn, ctx.journey_id)
        if journey is None or ctx.booking_status != "confirmed" or utc_now() >= ctx.start_at:
            raise app_error("booking_not_active")
        if not await slots.interviewer_has_badge(conn, interviewer_id, journey.badge_id):
            raise app_error("badge_mismatch")
        target = await admin_writes.free_slot_at(conn, interviewer_id, ctx.start_at)
        if target is None or not await slots.claim_open(conn, target):
            raise app_error("no_free_slot")
        name, link = await slots.interviewer_details(conn, interviewer_id)
        await admin_writes.move_booking(conn, booking_id, target, link)
        await slots.set_status(conn, ctx.slot_id, "blocked")
        meta = {"from_slot": ctx.slot_id, "to_slot": target}
        await transition(conn, journey, journey, Audit(actor, "admin_reassigned", meta))
    return ReassignResponse(booking_id=booking_id, slot_id=target, interviewer_name=name)
