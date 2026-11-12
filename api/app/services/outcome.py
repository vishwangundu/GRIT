"""Record and edit interview results (PRD I2, I3, FR-A6) in one transaction each.

Edits undo the previous result first: the journey is restored from prev_snapshot and a Pass
award is nullified with its Miles reversed by delta (not by overwriting the balance, so Miles
earned elsewhere in between are kept). Then the new result is applied as if fresh.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.clock import utc_now
from app.core.errors import app_error
from app.core.rules import MAX_ATTEMPTS, OUTCOME_EDIT_WINDOW, JourneyState
from app.db.session import Conn
from app.deps.auth import Actor
from app.repositories import awards, bookings, journeys, outcomes
from app.repositories.outcomes import OutcomeFields, OutcomeIn
from app.repositories.rows import BookingContext, JourneyRow, OutcomeRow
from app.schemas.outcome import OutcomeCreate, OutcomeEdit
from app.services import notify
from app.services.journey import Audit, persist_derived, transition
from app.services.outcome_rules import (
    RESULT_STATES,
    Effect,
    compute_effect,
    restore,
    snapshot,
    validate,
)


@dataclass(frozen=True)
class RecordedOutcome:
    outcome_id: UUID
    journey_state: JourneyState
    next_bookable_at: datetime | None
    attempts_used: int
    editable_until: datetime


@dataclass(frozen=True)
class Plan:
    ctx: BookingContext
    before: JourneyRow
    effect: Effect
    fields: OutcomeFields
    outcome_id: UUID


async def _context(conn: Conn, actor: Actor, booking_id: UUID) -> BookingContext:
    ctx = await bookings.get_context(conn, booking_id)
    if ctx is None:
        raise app_error("booking_not_found")
    if actor.role == "interviewer" and ctx.interviewer_id != actor.user_id:
        raise app_error("not_your_interview")
    return ctx


async def _lock_journey(conn: Conn, journey_id: UUID) -> JourneyRow:
    journey = await journeys.lock_by_id(conn, journey_id)
    if journey is None:
        raise app_error("booking_not_found")
    return journey


def _result(plan: Plan, editable_until: datetime) -> RecordedOutcome:
    after = plan.effect.journey
    return RecordedOutcome(
        outcome_id=plan.outcome_id,
        journey_state=after.state,
        next_bookable_at=after.next_bookable_at,
        attempts_used=after.attempts_used,
        editable_until=editable_until,
    )


async def record_outcome(
    conn: Conn, actor: Actor, booking_id: UUID, data: OutcomeCreate
) -> RecordedOutcome:
    now = utc_now()
    async with conn.transaction():
        ctx = await _context(conn, actor, booking_id)
        if now < ctx.start_at:
            raise app_error("interview_not_started")
        journey = await _lock_journey(conn, ctx.journey_id)
        if await outcomes.get_by_booking(conn, booking_id):
            raise app_error("outcome_exists")
        if ctx.booking_status != "confirmed" or journey.active_booking_id != booking_id:
            raise app_error("booking_not_active")
        fields = validate(data, now)
        journey = await persist_derived(conn, journey, now)
        miles = await awards.get_miles(conn, journey.student_id)
        effect = compute_effect(journey, fields, now)
        row = await outcomes.insert(
            conn,
            OutcomeIn(
                booking_id=booking_id,
                journey_id=journey.id,
                interviewer_id=ctx.interviewer_id,
                recorded_by=actor.user_id,
                fields=fields,
                prev_snapshot=snapshot(journey, miles),
                recorded_at=now,
                locked_at=now + OUTCOME_EDIT_WINDOW,
            ),
        )
        plan = Plan(ctx, journey, effect, fields, row.id)
        await _apply(conn, actor, plan)
    return _result(plan, row.locked_at)


def _check_edit_rights(actor: Actor, outcome: OutcomeRow, note: str | None, now: datetime) -> None:
    if actor.role == "admin":
        if not (note and note.strip()):
            raise app_error("edit_note_required")
        return
    if now >= outcome.locked_at:
        raise app_error("edit_window_closed")


async def edit_outcome(
    conn: Conn, actor: Actor, booking_id: UUID, data: OutcomeEdit
) -> RecordedOutcome:
    now = utc_now()
    async with conn.transaction():
        ctx = await _context(conn, actor, booking_id)
        journey = await _lock_journey(conn, ctx.journey_id)
        outcome = await outcomes.get_by_booking(conn, booking_id)
        if outcome is None:
            raise app_error("outcome_not_found")
        _check_edit_rights(actor, outcome, data.edit_note, now)
        fields = validate(data, now)
        if journey.state not in RESULT_STATES[outcome.result]:
            raise app_error("journey_moved_on")
        restored = await _undo(conn, actor, journey, outcome, now)
        effect = compute_effect(restored, fields, now)
        note = data.edit_note.strip() if data.edit_note else None
        await outcomes.update(conn, outcome.id, fields, (now, note))
        plan = Plan(ctx, restored, effect, fields, outcome.id)
        await _apply(conn, actor, plan)
    return _result(plan, outcome.locked_at)


async def _undo(
    conn: Conn, actor: Actor, journey: JourneyRow, outcome: OutcomeRow, now: datetime
) -> JourneyRow:
    if outcome.result == "pass":
        award = await awards.live_for_outcome(conn, outcome.id)
        if award is not None:
            await awards.nullify(conn, award.id, now, "outcome_edited")
            await awards.add_miles(conn, journey.student_id, -award.miles_awarded)
    restored = restore(journey, outcome.prev_snapshot)
    audit = Audit(actor, "outcome_edit_undo", {"outcome_id": outcome.id})
    return await transition(conn, journey, restored, audit)


async def _apply(conn: Conn, actor: Actor, plan: Plan) -> None:
    after = plan.effect.journey
    audit = Audit(actor, f"outcome_{plan.fields.result}", {"outcome_id": plan.outcome_id})
    await transition(conn, plan.before, after, audit)
    if plan.effect.miles:
        await awards.insert(
            conn, after.student_id, after.badge_id, plan.outcome_id, plan.effect.miles
        )
        await awards.add_miles(conn, after.student_id, plan.effect.miles)
    await bookings.set_status(conn, plan.ctx.booking_id, plan.effect.booking_status)
    await _notify_result(conn, plan)


async def _notify_result(conn: Conn, plan: Plan) -> None:
    after = plan.effect.journey
    values = await notify.badge_vars(conn, after.badge_id, after.student_id)
    values |= {
        "feedback": plan.fields.feedback_to_student,
        "miles": str(plan.effect.miles),
        "attempts_left": str(MAX_ATTEMPTS - after.attempts_used),
        "date": notify.ist_date(plan.ctx.start_at),
        "start": notify.ist_time(plan.ctx.start_at),
    }
    if after.next_bookable_at:
        rebook = notify.ist_date(after.next_bookable_at)
        values |= {"retake_date": rebook, "rebook_date": rebook}
    payload = {"outcome_id": str(plan.outcome_id), "booking_id": str(plan.ctx.booking_id)}
    await notify.send(conn, after.student_id, plan.effect.template, values, payload)
