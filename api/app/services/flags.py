"""Malpractice flags (A4): raise -> under_review; uphold -> nullified; dismiss -> passed.
Uphold nullifies the badge and reverses its Miles in the same transaction."""

from uuid import UUID

from app.core.clock import utc_now
from app.core.errors import app_error
from app.db.session import Conn
from app.deps.auth import Actor
from app.repositories import admin_writes, awards, journeys
from app.repositories.rows import JourneyRow
from app.schemas.admin import FlagCreate, FlagCreated, FlagDecided, FlagDecision
from app.services import notify
from app.services.journey import Audit, transition


async def _lock_journey(conn: Conn, student_id: UUID, badge_id: int) -> JourneyRow:
    journey_id = await admin_writes.journey_id_for(conn, student_id, badge_id)
    journey = await journeys.lock_by_id(conn, journey_id) if journey_id else None
    if journey is None:
        raise app_error("student_not_found")
    return journey


async def raise_flag(conn: Conn, actor: Actor, body: FlagCreate) -> FlagCreated:
    async with conn.transaction():
        journey = await _lock_journey(conn, body.student_id, body.badge_id)
        award = await admin_writes.live_award(conn, body.student_id, body.badge_id)
        if journey.state != "passed" or award is None or award.status != "active":
            raise app_error("not_passed")
        flag_id = await admin_writes.insert_flag(
            conn, award.id, body.student_id, actor.user_id, (body.source, body.evidence_url)
        )
        await admin_writes.set_award_status(conn, award.id, "under_review")
        after = journey.model_copy(update={"state": "under_review"})
        await transition(conn, journey, after, Audit(actor, "flag_raised", {"flag_id": flag_id}))
        values = await notify.badge_vars(conn, journey.badge_id, journey.student_id)
        await notify.send(conn, journey.student_id, "under_review", values)
    return FlagCreated(flag_id=flag_id, journey_state="under_review")


async def decide_flag(conn: Conn, actor: Actor, flag_id: UUID, body: FlagDecision) -> FlagDecided:
    now = utc_now()
    async with conn.transaction():
        flag = await admin_writes.lock_flag(conn, flag_id)
        if flag is None:
            raise app_error("flag_not_found")
        if flag.status != "open":
            raise app_error("flag_closed")
        award = await admin_writes.award_by_id(conn, flag.badge_award_id)
        if award is None:
            raise app_error("flag_not_found")
        journey = await _lock_journey(conn, flag.student_id, award.badge_id)
        values = await notify.badge_vars(conn, journey.badge_id, journey.student_id)
        is_uphold = body.decision == "uphold"
        if is_uphold:
            await admin_writes.set_award_status(conn, award.id, "nullified", (now, body.note))
            await awards.add_miles(conn, flag.student_id, -award.miles_awarded)
            values["miles"] = str(award.miles_awarded)
        else:
            await admin_writes.set_award_status(conn, award.id, "active")
        state = "nullified" if is_uphold else "passed"
        after = journey.model_copy(update={"state": state})
        meta = {"flag_id": flag_id, "note": body.note}
        await transition(conn, journey, after, Audit(actor, f"flag_{body.decision}", meta))
        decision = ("upheld" if is_uphold else "dismissed", actor.user_id, body.note)
        await admin_writes.decide_flag(conn, flag_id, decision, now)
        template = "nullified" if is_uphold else "review_dismissed"
        await notify.send(conn, journey.student_id, template, values)
    return FlagDecided(
        flag_id=flag_id,
        journey_state=after.state,
        award_status="nullified" if is_uphold else "active",
    )
