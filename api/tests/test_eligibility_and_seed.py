"""Eligibility recompute (section 3 first row, section 9 skill revoked) and the demo seed."""

import asyncpg

from app.seed.run import seed_demo
from app.seed.users import LocalProvisioner
from app.services import eligibility
from tests.factories import World, hours_from_now, make_booking, make_slot, make_student

EXPECTED_SEED_STATES = {
    "aarav": "eligible",
    "sneha": "awaiting_result",
    "divya": "awaiting_result",
    "rohan": "booked",
    "ishita": "booked",
    "kavya": "awaiting_result",
    "pooja": "retake_later",
    "arjun": "failed",
    "meera": "passed",
    "nikhil": "under_review",
    "tanvi": "eligible",
    "ananya": "eligible",
    "harsha": "eligible",
    "lakshmi": "not_eligible",
    "ravi": "locked",
    "sana": "nullified",
}


async def test_clearing_last_skill_makes_student_eligible(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world, state="not_eligible")

        result = await eligibility.recompute(conn, student.actor.user_id)

        assert result.journeys[0].state == "eligible"
        title = await conn.fetchval("select title from notifications where template = 'eligible'")
        assert title == "You’re interview-ready"


async def test_revoked_skill_cancels_booking_and_reopens_slot(
    db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        slot_id = await make_slot(conn, world.interviewer, hours_from_now(24))
        booking_id = await make_booking(conn, student, slot_id)
        await conn.execute(
            "update student_skill_levels set status = 'revoked' "
            "where student_id = $1 and skill_id = 4",
            student.actor.user_id,
        )

        result = await eligibility.recompute(conn, student.actor.user_id)

        assert result.journeys[0].state == "not_eligible"
        status = await conn.fetchval("select status from bookings where id = $1", booking_id)
        assert status == "cancelled_by_system"
        assert await conn.fetchval("select status from slots where id = $1", slot_id) == "open"


async def test_demo_seed_puts_every_student_in_prd_state(db: asyncpg.Pool) -> None:
    async with db.acquire() as conn, conn.transaction():
        result = await seed_demo(conn, LocalProvisioner(conn))
        rows = await conn.fetch(
            """
            select split_part(p.email, '@', 1) as who, v.effective_state
            from v_journey_effective v join profiles p on p.id = v.student_id
            """
        )
    assert result.students == 56
    assert {r["who"]: r["effective_state"] for r in rows} == EXPECTED_SEED_STATES
