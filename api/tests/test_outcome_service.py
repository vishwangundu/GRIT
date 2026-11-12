"""Recording and editing results (PRD I2, I3, FR-A6, section 3 side effects)."""

from datetime import timedelta

import asyncpg
import pytest

from app.core.clock import utc_now
from app.core.errors import AppError
from app.core.rules import IST, MAX_ATTEMPTS, PASS_MILES
from app.schemas.outcome import OutcomeCreate, OutcomeEdit
from app.services import outcome
from tests.factories import StudentRef, World, hours_from_now, make_booking, make_slot, make_student

RUBRIC = {"problem_solving": 3, "product_thinking": 2, "code_walkthrough": 2, "communication": 3}
FEEDBACK = "Walk me through one project end to end, including how you tested it."
START_MILES = 2340


def _pass() -> OutcomeCreate:
    return OutcomeCreate(result="pass", rubric=RUBRIC, feedback_to_student="Great demo.")


def _fail() -> OutcomeCreate:
    return OutcomeCreate(result="fail", rubric=RUBRIC, feedback_to_student=FEEDBACK)


async def _started_interview(
    conn: asyncpg.Connection, world: World, **journey: object
) -> tuple[StudentRef, object]:
    student = await make_student(conn, world, **journey)
    slot_id = await make_slot(conn, world.interviewer, hours_from_now(-0.75))
    return student, await make_booking(conn, student, slot_id)


async def _journey(conn: asyncpg.Connection, student: StudentRef) -> asyncpg.Record:
    row = await conn.fetchrow(
        "select state, attempts_used, next_bookable_at from interview_journeys where id = $1",
        student.journey_id,
    )
    assert row is not None
    return row


async def _miles(conn: asyncpg.Connection, student: StudentRef) -> int:
    return int(
        await conn.fetchval("select miles from students where id = $1", student.actor.user_id)
    )


async def _templates(conn: asyncpg.Connection, student: StudentRef) -> list[str]:
    rows = await conn.fetch(
        "select template from notifications where user_id = $1 order by created_at",
        student.actor.user_id,
    )
    return [r["template"] for r in rows]


async def test_pass_awards_badge_and_miles(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student, booking_id = await _started_interview(conn, world)

        result = await outcome.record_outcome(conn, world.interviewer, booking_id, _pass())

        assert result.journey_state == "passed"
        assert result.editable_until - utc_now() > timedelta(hours=1, minutes=59)
        assert await _miles(conn, student) == START_MILES + PASS_MILES
        award = await conn.fetchval(
            "select status from badge_awards where student_id = $1", student.actor.user_id
        )
        assert award == "active"
        note = await conn.fetchrow("select title, body from notifications where template = 'pass'")
        assert note is not None
        assert note["title"] == "Novice Badge unlocked. You cleared the interview!"
        assert note["body"].endswith(
            "Next stop: Specialist Badge. You have cleared 1 of its 2 skills."
        )
        status = await conn.fetchval("select status from bookings where id = $1", booking_id)
        assert status == "completed"


async def test_retake_later_uses_no_attempt_and_rebooks_from_midnight_ist(
    db: asyncpg.Pool, world: World
) -> None:
    retake_day = (utc_now() + timedelta(days=3)).astimezone(IST).date()
    async with db.acquire() as conn:
        student, booking_id = await _started_interview(conn, world)
        data = OutcomeCreate(
            result="retake_later",
            rubric=RUBRIC,
            feedback_to_student=FEEDBACK,
            retake_after=retake_day,
        )

        result = await outcome.record_outcome(conn, world.interviewer, booking_id, data)

        assert (result.journey_state, result.attempts_used) == ("retake_later", 0)
        assert result.next_bookable_at is not None
        local = result.next_bookable_at.astimezone(IST)
        assert (local.date(), local.hour, local.minute) == (retake_day, 0, 0)
        assert await _templates(conn, student) == ["retake"]


async def test_fail_uses_attempt_and_sets_14_day_cooldown(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        _, booking_id = await _started_interview(conn, world)

        result = await outcome.record_outcome(conn, world.interviewer, booking_id, _fail())

        assert (result.journey_state, result.attempts_used) == ("failed", 1)
        assert result.next_bookable_at is not None
        assert result.next_bookable_at - utc_now() > timedelta(days=13, hours=23)
        body = await conn.fetchval("select body from notifications where template = 'fail'")
        assert body.endswith("You have 2 attempts left.")


async def test_no_show_uses_attempt_with_7_day_cooldown(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student, booking_id = await _started_interview(conn, world)

        result = await outcome.record_outcome(
            conn, world.interviewer, booking_id, OutcomeCreate(result="no_show")
        )

        assert (result.journey_state, result.attempts_used) == ("failed", 1)
        assert result.next_bookable_at is not None
        assert timedelta(days=6) < result.next_bookable_at - utc_now() <= timedelta(days=7)
        status = await conn.fetchval("select status from bookings where id = $1", booking_id)
        assert status == "no_show"
        assert await _templates(conn, student) == ["no_show"]


async def test_third_fail_locks_journey(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student, booking_id = await _started_interview(conn, world, attempts_used=MAX_ATTEMPTS - 1)

        result = await outcome.record_outcome(conn, world.interviewer, booking_id, _fail())

        assert (result.journey_state, result.attempts_used) == ("locked", MAX_ATTEMPTS)
        assert result.next_bookable_at is None
        assert await _templates(conn, student) == ["locked"]


async def test_result_before_slot_start_is_rejected(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        booking_id = await make_booking(
            conn, student, await make_slot(conn, world.interviewer, hours_from_now(1))
        )
        with pytest.raises(AppError) as err:
            await outcome.record_outcome(conn, world.interviewer, booking_id, _pass())
        assert err.value.code == "interview_not_started"


async def test_second_result_returns_outcome_exists(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        _, booking_id = await _started_interview(conn, world)
        await outcome.record_outcome(conn, world.interviewer, booking_id, _pass())
        with pytest.raises(AppError) as err:
            await outcome.record_outcome(conn, world.interviewer, booking_id, _pass())
        assert (err.value.code, err.value.http_status) == ("outcome_exists", 409)


async def test_other_interviewer_cannot_record_result(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        _, booking_id = await _started_interview(conn, world)
        with pytest.raises(AppError) as err:
            await outcome.record_outcome(conn, world.uncleared_interviewer, booking_id, _pass())
        assert err.value.code == "not_your_interview"


async def test_edit_pass_to_fail_reverses_miles_and_award(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student, booking_id = await _started_interview(conn, world)
        await outcome.record_outcome(conn, world.interviewer, booking_id, _pass())

        result = await outcome.edit_outcome(
            conn, world.interviewer, booking_id, OutcomeEdit(**_fail().model_dump())
        )

        assert (result.journey_state, result.attempts_used) == ("failed", 1)
        assert await _miles(conn, student) == START_MILES
        statuses = await conn.fetch(
            "select status from badge_awards where student_id = $1", student.actor.user_id
        )
        assert [r["status"] for r in statuses] == ["nullified"]
        edited = await conn.fetchval(
            "select edited_at is not null from interview_outcomes where booking_id = $1",
            booking_id,
        )
        assert edited is True


async def test_edit_fail_to_pass_gives_attempt_back(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student, booking_id = await _started_interview(conn, world, attempts_used=1)
        await outcome.record_outcome(conn, world.interviewer, booking_id, _fail())

        result = await outcome.edit_outcome(
            conn, world.interviewer, booking_id, OutcomeEdit(**_pass().model_dump())
        )

        assert (result.journey_state, result.attempts_used) == ("passed", 1)
        assert await _miles(conn, student) == START_MILES + PASS_MILES


async def test_interviewer_edit_after_two_hours_returns_edit_window_closed(
    db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        _, booking_id = await _started_interview(conn, world)
        await outcome.record_outcome(conn, world.interviewer, booking_id, _pass())
        await conn.execute(
            "update interview_outcomes set locked_at = now() - interval '1 minute' "
            "where booking_id = $1",
            booking_id,
        )
        with pytest.raises(AppError) as err:
            await outcome.edit_outcome(
                conn, world.interviewer, booking_id, OutcomeEdit(**_fail().model_dump())
            )
        assert (err.value.code, err.value.http_status) == ("edit_window_closed", 403)


async def test_admin_can_edit_after_window_only_with_note(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        _, booking_id = await _started_interview(conn, world)
        await outcome.record_outcome(conn, world.interviewer, booking_id, _pass())
        await conn.execute("update interview_outcomes set locked_at = now() - interval '1 minute'")
        without_note = OutcomeEdit(**_fail().model_dump())
        with pytest.raises(AppError) as err:
            await outcome.edit_outcome(conn, world.admin, booking_id, without_note)
        assert err.value.code == "edit_note_required"

        with_note = OutcomeEdit(**_fail().model_dump(), edit_note="Recording error, see ticket.")
        result = await outcome.edit_outcome(conn, world.admin, booking_id, with_note)
        assert result.journey_state == "failed"


async def test_edit_after_journey_moved_on_is_rejected(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student, booking_id = await _started_interview(conn, world)
        await outcome.record_outcome(conn, world.interviewer, booking_id, _pass())
        await conn.execute(
            "update interview_journeys set state = 'under_review' where id = $1",
            student.journey_id,
        )
        with pytest.raises(AppError) as err:
            await outcome.edit_outcome(
                conn, world.interviewer, booking_id, OutcomeEdit(**_fail().model_dump())
            )
        assert err.value.code == "journey_moved_on"


async def test_edit_without_result_returns_outcome_not_found(
    db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        _, booking_id = await _started_interview(conn, world)
        with pytest.raises(AppError) as err:
            await outcome.edit_outcome(
                conn, world.interviewer, booking_id, OutcomeEdit(**_pass().model_dump())
            )
        assert err.value.code == "outcome_not_found"
