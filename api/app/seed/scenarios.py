"""Puts each named demo student into their PRD section 11 state through the real services
wherever the rules allow; bookings in the past or under 6 h are inserted directly."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from uuid import UUID

from app.core.clock import utc_now
from app.core.errors import app_error
from app.core.rules import IST
from app.db.session import Conn
from app.deps.auth import Actor
from app.repositories import bookings, journeys, slots
from app.repositories.bookings import BookingIn
from app.schemas.admin import FlagCreate, FlagDecision
from app.schemas.outcome import OutcomeCreate
from app.seed.setup import ist_at
from app.services import booking, flags, outcome
from app.services.journey import Audit, transition

RUBRIC_GOOD = {
    "problem_solving": 4,
    "product_thinking": 3,
    "code_walkthrough": 4,
    "communication": 3,
}
RUBRIC_WEAK = {
    "problem_solving": 2,
    "product_thinking": 2,
    "code_walkthrough": 1,
    "communication": 2,
}
PRAISE_FEEDBACK = "Clear walkthrough of your project and sharp answers on trade-offs."
FEEDBACK_RETAKE = "Walk me through one project end to end, including how you tested it."
FEEDBACK_FAIL = "Revise prompt design basics and practise explaining your code out loud."


@dataclass(frozen=True)
class Cast:
    admin: Actor
    priya: Actor
    rahul: Actor
    badge_id: int


async def slot_at(conn: Conn, interviewer: Actor, start_at: datetime) -> UUID:
    found = await conn.fetchval(
        "select id from slots where interviewer_id = $1 and start_at = $2",
        interviewer.user_id,
        start_at,
    )
    if found is None:
        raise RuntimeError(f"seed slot missing at {start_at.isoformat()}")
    return UUID(str(found))


async def first_open_slot(conn: Conn, interviewer: Actor, after: datetime) -> UUID:
    found = await conn.fetchval(
        "select id from slots where interviewer_id = $1 and start_at >= $2 and status = 'open' "
        "order by start_at limit 1",
        interviewer.user_id,
        after,
    )
    if found is None:
        raise RuntimeError("seed: no open slot found")
    return UUID(str(found))


async def force_booking(conn: Conn, student_id: UUID, slot_id: UUID) -> UUID:
    """Book a slot that the student API would refuse (in the past or under 6 h away)."""
    journey = (await journeys.lock_for_student(conn, student_id))[0]
    slot = await slots.get(conn, slot_id)
    if slot is None or not await slots.claim_open(conn, slot_id):
        raise app_error("slot_taken")
    _, link = await slots.interviewer_details(conn, slot.interviewer_id)
    booking_id = await bookings.insert(conn, BookingIn(journey.id, slot_id, student_id, 0, link))
    after = journey.model_copy(update={"state": "booked", "active_booking_id": booking_id})
    await transition(conn, journey, after, Audit(actor=None, reason="seed_booking"))
    return booking_id


async def backdate_outcome(conn: Conn, booking_id: UUID) -> None:
    """Make a seeded result look recorded 30 min after its slot ended (edit window closed)."""
    await conn.execute(
        """
        update interview_outcomes o
        set recorded_at = s.end_at + interval '30 minutes',
            locked_at = s.end_at + interval '150 minutes'
        from bookings b join slots s on s.id = b.slot_id
        where o.booking_id = b.id and b.id = $1
        """,
        booking_id,
    )


async def interviewed(
    conn: Conn, cast: Cast, student_id: UUID, start_at: datetime, result: OutcomeCreate
) -> UUID:
    booking_id = await force_booking(conn, student_id, await slot_at(conn, cast.priya, start_at))
    await outcome.record_outcome(conn, cast.priya, booking_id, result)
    await backdate_outcome(conn, booking_id)
    return booking_id


def pass_result() -> OutcomeCreate:
    return OutcomeCreate(result="pass", rubric=RUBRIC_GOOD, feedback_to_student=PRAISE_FEEDBACK)


async def flagged(conn: Conn, cast: Cast, student_id: UUID, start_at: datetime) -> UUID:
    await interviewed(conn, cast, student_id, start_at, pass_result())
    body = FlagCreate(student_id=student_id, badge_id=cast.badge_id, source="proctoring report")
    created = await flags.raise_flag(conn, cast.admin, body)
    return created.flag_id


async def apply_states(
    conn: Conn, cast: Cast, ids: dict[str, UUID], days: tuple[date, date, datetime]
) -> None:
    """days = (yesterday, two days ago, today's first Priya slot start)."""
    yesterday, two_ago, today_first = days
    now_slot = today_first + timedelta(hours=2)
    await force_booking(conn, ids["sneha"], await slot_at(conn, cast.priya, today_first))
    await force_booking(conn, ids["divya"], await slot_at(conn, cast.priya, now_slot))
    await force_booking(
        conn, ids["rohan"], await slot_at(conn, cast.priya, now_slot + timedelta(minutes=30))
    )
    student = Actor(user_id=ids["ishita"], role="student")
    rahul_slot = await first_open_slot(conn, cast.rahul, utc_now() + timedelta(days=2))
    await booking.book_slot(conn, student, rahul_slot)
    await force_booking(conn, ids["kavya"], await slot_at(conn, cast.priya, ist_at(two_ago, 10)))
    retake = OutcomeCreate(
        result="retake_later",
        rubric=RUBRIC_WEAK,
        feedback_to_student=FEEDBACK_RETAKE,
        retake_after=(utc_now().astimezone(IST) + timedelta(days=2)).date(),
    )
    await interviewed(conn, cast, ids["pooja"], ist_at(yesterday, 10), retake)
    fail = OutcomeCreate(result="fail", rubric=RUBRIC_WEAK, feedback_to_student=FEEDBACK_FAIL)
    await interviewed(conn, cast, ids["arjun"], ist_at(yesterday, 10, 30), fail)
    await interviewed(conn, cast, ids["meera"], ist_at(yesterday, 11), pass_result())
    await flagged(conn, cast, ids["nikhil"], ist_at(two_ago, 10, 30))
    await conn.execute(
        "update interview_journeys set attempts_used = 2 where student_id = $1", ids["ravi"]
    )
    await interviewed(conn, cast, ids["ravi"], ist_at(two_ago, 11), fail)
    sana_flag = await flagged(conn, cast, ids["sana"], ist_at(two_ago, 11, 30))
    decision = FlagDecision(decision="uphold", note="Proctoring evidence confirmed.")
    await flags.decide_flag(conn, cast.admin, sana_flag, decision)
    harsha = Actor(user_id=ids["harsha"], role="student")
    harsha_slot = await first_open_slot(conn, cast.priya, utc_now() + timedelta(hours=8))
    await booking.book_slot(conn, harsha, harsha_slot)
    await booking.cancel_by_interviewer(conn, cast.priya, harsha_slot, "illness")
