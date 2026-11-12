"""Booking, rescheduling and cancelling (PRD S1-S4, I4, section 9 edge cases)."""

import asyncio

import asyncpg
import pytest

from app.core.errors import AppError
from app.core.rules import RESCHEDULE_MAX
from app.services import booking
from tests.factories import (
    MEET_LINK,
    StudentRef,
    World,
    hours_from_now,
    make_booking,
    make_slot,
    make_student,
)


async def _state(conn: asyncpg.Connection, student: StudentRef) -> tuple[str, bool]:
    row = await conn.fetchrow(
        "select state, priority from interview_journeys where id = $1", student.journey_id
    )
    assert row is not None
    return row["state"], row["priority"]


async def _slot_status(conn: asyncpg.Connection, slot_id: object) -> str:
    return str(await conn.fetchval("select status from slots where id = $1", slot_id))


async def test_eligible_student_books_open_slot(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        slot_id = await make_slot(conn, world.interviewer, hours_from_now(24))

        result = await booking.book_slot(conn, student.actor, slot_id)

        assert result.state == "booked"
        assert result.reschedules_left == RESCHEDULE_MAX
        assert result.interviewer_name == "Priya Sharma"
        assert result.meeting_link == MEET_LINK
        assert await _state(conn, student) == ("booked", False)
        assert await _slot_status(conn, slot_id) == "booked"
        note = await conn.fetchrow(
            "select title, body from notifications where user_id = $1", student.actor.user_id
        )
        assert note is not None
        assert note["title"] == "Your interview is booked"
        assert note["body"].startswith("AI Product Mastery, Novice Badge. ")
        event = await conn.fetchrow(
            "select from_state, to_state, actor_role, reason from journey_events "
            "where journey_id = $1",
            student.journey_id,
        )
        assert event is not None
        assert dict(event) == {
            "from_state": "eligible",
            "to_state": "booked",
            "actor_role": "student",
            "reason": "student_booked",
        }


@pytest.mark.parametrize("round_no", range(5))
async def test_second_booking_on_same_slot_returns_409(
    db: asyncpg.Pool, world: World, round_no: int
) -> None:
    async with db.acquire() as conn:
        first = await make_student(conn, world)
        second = await make_student(conn, world)
        slot_id = await make_slot(conn, world.interviewer, hours_from_now(30 + round_no))

    async def attempt(student: StudentRef) -> str:
        async with db.acquire() as conn:
            try:
                await booking.book_slot(conn, student.actor, slot_id)
            except AppError as exc:
                return exc.code
            return "booked"

    outcomes = await asyncio.gather(attempt(first), attempt(second))

    assert sorted(outcomes) == ["booked", "slot_taken"]
    async with db.acquire() as conn:
        confirmed = await conn.fetchval(
            "select count(*) from bookings where slot_id = $1 and status = 'confirmed'", slot_id
        )
        assert confirmed == 1


@pytest.mark.parametrize(
    ("hours_ahead", "code"),
    [(5.5, "too_soon"), (24 * 14 + 1, "too_far")],
)
async def test_slot_outside_booking_window_is_rejected(
    db: asyncpg.Pool, world: World, hours_ahead: float, code: str
) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        slot_id = await make_slot(conn, world.interviewer, hours_from_now(hours_ahead))
        with pytest.raises(AppError) as err:
            await booking.book_slot(conn, student.actor, slot_id)
        assert err.value.code == code
        assert await _slot_status(conn, slot_id) == "open"


@pytest.mark.parametrize("state", ["not_eligible", "passed", "locked", "under_review"])
async def test_student_who_is_not_eligible_cannot_book(
    db: asyncpg.Pool, world: World, state: str
) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world, state=state)
        slot_id = await make_slot(conn, world.interviewer, hours_from_now(24))
        with pytest.raises(AppError) as err:
            await booking.book_slot(conn, student.actor, slot_id)
        assert (err.value.code, err.value.http_status) == ("not_eligible", 403)


async def test_failed_student_can_rebook_once_cooldown_has_ended(
    db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        student = await make_student(
            conn, world, state="failed", attempts_used=1, next_bookable_at=hours_from_now(-1)
        )
        slot_id = await make_slot(conn, world.interviewer, hours_from_now(24))

        await booking.book_slot(conn, student.actor, slot_id)

        events = await conn.fetch(
            "select from_state, to_state, actor_role from journey_events "
            "where journey_id = $1 order by id",
            student.journey_id,
        )
        assert [tuple(e) for e in events] == [
            ("failed", "eligible", "system"),
            ("eligible", "booked", "student"),
        ]


async def test_failed_student_in_cooldown_cannot_book(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student = await make_student(
            conn, world, state="failed", attempts_used=1, next_bookable_at=hours_from_now(48)
        )
        slot_id = await make_slot(conn, world.interviewer, hours_from_now(24))
        with pytest.raises(AppError) as err:
            await booking.book_slot(conn, student.actor, slot_id)
        assert err.value.code == "not_eligible"


async def test_interviewer_not_cleared_for_badge_returns_badge_mismatch(
    db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        slot_id = await make_slot(conn, world.uncleared_interviewer, hours_from_now(24))
        with pytest.raises(AppError) as err:
            await booking.book_slot(conn, student.actor, slot_id)
        assert err.value.code == "badge_mismatch"


async def test_reschedule_reopens_old_slot_and_counts(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        old_slot = await make_slot(conn, world.interviewer, hours_from_now(24))
        new_slot = await make_slot(conn, world.interviewer, hours_from_now(48))
        old_booking = await make_booking(conn, student, old_slot)

        result = await booking.book_slot(conn, student.actor, new_slot)

        assert result.reschedules_left == RESCHEDULE_MAX - 1
        assert await _slot_status(conn, old_slot) == "open"
        assert await _slot_status(conn, new_slot) == "booked"
        old_status = await conn.fetchval("select status from bookings where id = $1", old_booking)
        assert old_status == "rescheduled"
        count = await conn.fetchval(
            "select reschedule_count from bookings where id = $1", result.booking_id
        )
        assert count == 1


async def test_third_reschedule_returns_reschedule_limit(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        current = await make_slot(conn, world.interviewer, hours_from_now(24))
        await make_booking(conn, student, current, reschedule_count=RESCHEDULE_MAX)
        new_slot = await make_slot(conn, world.interviewer, hours_from_now(48))
        with pytest.raises(AppError) as err:
            await booking.book_slot(conn, student.actor, new_slot)
        assert err.value.code == "reschedule_limit"
        assert await _slot_status(conn, new_slot) == "open"


async def test_reschedule_within_12_hours_returns_change_window_closed(
    db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        current = await make_slot(conn, world.interviewer, hours_from_now(11))
        await make_booking(conn, student, current)
        new_slot = await make_slot(conn, world.interviewer, hours_from_now(48))
        with pytest.raises(AppError) as err:
            await booking.book_slot(conn, student.actor, new_slot)
        assert err.value.code == "change_window_closed"


async def test_student_cancel_returns_to_eligible_without_using_attempt(
    db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        slot_id = await make_slot(conn, world.interviewer, hours_from_now(24))
        booking_id = await make_booking(conn, student, slot_id)

        assert await booking.cancel_by_student(conn, student.actor) == "eligible"

        assert await _state(conn, student) == ("eligible", False)
        assert await _slot_status(conn, slot_id) == "open"
        status = await conn.fetchval("select status from bookings where id = $1", booking_id)
        assert status == "cancelled_by_student"
        attempts = await conn.fetchval(
            "select attempts_used from interview_journeys where id = $1", student.journey_id
        )
        assert attempts == 0


async def test_student_cancel_within_12_hours_is_rejected(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        await make_booking(
            conn, student, await make_slot(conn, world.interviewer, hours_from_now(3))
        )
        with pytest.raises(AppError) as err:
            await booking.cancel_by_student(conn, student.actor)
        assert (err.value.code, err.value.http_status) == ("change_window_closed", 422)


async def test_cancel_without_booking_returns_no_booking(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        with pytest.raises(AppError) as err:
            await booking.cancel_by_student(conn, student.actor)
        assert (err.value.code, err.value.http_status) == ("no_booking", 404)


async def test_interviewer_cancel_gives_student_priority_and_notifies(
    db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        slot_id = await make_slot(conn, world.interviewer, hours_from_now(4))
        await make_booking(conn, student, slot_id)

        notified = await booking.cancel_by_interviewer(conn, world.interviewer, slot_id, "illness")

        assert notified is True
        assert await _state(conn, student) == ("eligible", True)
        assert await _slot_status(conn, slot_id) == "cancelled"
        body = await conn.fetchval(
            "select body from notifications where user_id = $1 and template = 'iv_cancelled'",
            student.actor.user_id,
        )
        assert body.startswith("Your interviewer can’t make it (illness).")


async def test_interviewer_cannot_cancel_another_interviewers_slot(
    db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        slot_id = await make_slot(conn, world.interviewer, hours_from_now(24))
        await make_booking(conn, student, slot_id)
        with pytest.raises(AppError) as err:
            await booking.cancel_by_interviewer(
                conn, world.uncleared_interviewer, slot_id, "illness"
            )
        assert err.value.code == "not_your_interview"


async def test_booking_after_priority_cancel_clears_priority(
    db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world, priority=True)
        slot_id = await make_slot(conn, world.interviewer, hours_from_now(24))
        await booking.book_slot(conn, student.actor, slot_id)
        assert await _state(conn, student) == ("booked", False)
