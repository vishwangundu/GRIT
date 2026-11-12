"""Admin tracker, nudges, reminders, reassignment and malpractice flags (A1 to A4, FR-A6)."""

import asyncpg
import pytest

from app.core.errors import AppError
from app.core.rules import PASS_MILES
from app.schemas.admin import FlagCreate, FlagDecision, NudgeRequest
from app.schemas.outcome import OutcomeCreate
from app.services import admin_actions, flags, outcome, reminders, tracker
from tests.factories import (
    StudentRef,
    World,
    hours_from_now,
    make_booking,
    make_interviewer,
    make_slot,
    make_student,
)

RUBRIC = {"problem_solving": 3, "product_thinking": 3, "code_walkthrough": 3, "communication": 3}
START_MILES = 2340


async def _passed(conn: asyncpg.Connection, world: World) -> StudentRef:
    student = await make_student(conn, world)
    booking_id = await make_booking(
        conn, student, await make_slot(conn, world.interviewer, hours_from_now(-1))
    )
    await outcome.record_outcome(
        conn, world.interviewer, booking_id, OutcomeCreate(result="pass", rubric=RUBRIC)
    )
    return student


async def test_tracker_counts_tiles_and_marks_slow(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        waiting = await make_student(conn, world)
        await conn.execute(
            "update interview_journeys set eligible_at = now() - interval '9 days' where id = $1",
            waiting.journey_id,
        )
        booked = await make_student(conn, world)
        await make_booking(
            conn, booked, await make_slot(conn, world.interviewer, hours_from_now(24))
        )
        late = await make_student(conn, world)
        await make_booking(
            conn, late, await make_slot(conn, world.interviewer, hours_from_now(-30))
        )

        response = await tracker.get_tracker(conn, None, "notbooked")

        tiles = response.tiles
        assert (tiles.not_booked, tiles.booked, tiles.awaiting, tiles.awaiting_overdue) == (
            1,
            1,
            1,
            1,
        )
        row = response.not_booked_rows[0]
        assert (row.status, row.days_since_eligible, row.is_slow) == ("not_booked", 9, True)
        awaiting = await tracker.get_tracker(conn, world.badge_id, "awaiting")
        assert awaiting.awaiting_rows[0].status == "overdue"


async def test_nudge_is_sent_at_most_once_per_day(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        body = NudgeRequest(student_ids=[student.actor.user_id])

        first = await admin_actions.send_nudges(conn, body)
        second = await admin_actions.send_nudges(conn, body)

        assert (first.sent, first.skipped_recent) == (1, 0)
        assert (second.sent, second.skipped_recent) == (0, 1)
        text = await conn.fetchval("select body from notifications where template = 'nudge'")
        assert text.startswith("You became interview-ready 2 days ago.")


async def test_bulk_nudge_targets_students_waiting_seven_days(
    db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        old = await make_student(conn, world)
        await make_student(conn, world)
        await conn.execute(
            "update interview_journeys set eligible_at = now() - interval '8 days' where id = $1",
            old.journey_id,
        )
        result = await admin_actions.send_nudges(conn, NudgeRequest(min_days_waiting=7))
        assert result.sent == 1


async def test_uphold_nullifies_badge_and_reverses_miles(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student = await _passed(conn, world)
        body = FlagCreate(
            student_id=student.actor.user_id, badge_id=world.badge_id, source="proctoring report"
        )
        created = await flags.raise_flag(conn, world.admin, body)
        assert created.journey_state == "under_review"

        decided = await flags.decide_flag(
            conn, world.admin, created.flag_id, FlagDecision(decision="uphold", note="Confirmed.")
        )

        assert (decided.journey_state, decided.award_status) == ("nullified", "nullified")
        miles = await conn.fetchval(
            "select miles from students where id = $1", student.actor.user_id
        )
        assert miles == START_MILES
        templates = await conn.fetch(
            "select template from notifications where user_id = $1 order by created_at",
            student.actor.user_id,
        )
        assert [t["template"] for t in templates] == ["pass", "under_review", "nullified"]


async def test_dismiss_restores_passed_and_keeps_miles(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student = await _passed(conn, world)
        body = FlagCreate(student_id=student.actor.user_id, badge_id=world.badge_id, source="tip")
        created = await flags.raise_flag(conn, world.admin, body)
        decided = await flags.decide_flag(
            conn, world.admin, created.flag_id, FlagDecision(decision="dismiss", note="No issue.")
        )
        assert (decided.journey_state, decided.award_status) == ("passed", "active")
        miles = await conn.fetchval(
            "select miles from students where id = $1", student.actor.user_id
        )
        assert miles == START_MILES + PASS_MILES
        with pytest.raises(AppError) as err:
            await flags.decide_flag(
                conn, world.admin, created.flag_id, FlagDecision(decision="uphold", note="Again.")
            )
        assert err.value.code == "flag_closed"


async def test_flag_on_unpassed_student_returns_not_passed(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        body = FlagCreate(student_id=student.actor.user_id, badge_id=world.badge_id, source="tip")
        with pytest.raises(AppError) as err:
            await flags.raise_flag(conn, world.admin, body)
        assert (err.value.code, err.value.http_status) == ("not_passed", 422)


async def test_reassign_moves_booking_to_free_interviewer(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        start = hours_from_now(30)
        student = await make_student(conn, world)
        old_slot = await make_slot(conn, world.interviewer, start)
        booking_id = await make_booking(conn, student, old_slot)
        rahul = await make_interviewer(conn, "Rahul Verma", world.badge_id)
        new_slot = await make_slot(conn, rahul, start)

        options = await admin_actions.reassign_options(conn, booking_id)
        moved = await admin_actions.reassign(conn, world.admin, booking_id, rahul.user_id)

        assert [o.name for o in options.options] == ["Rahul Verma"]
        assert (moved.slot_id, moved.interviewer_name) == (new_slot, "Rahul Verma")
        old_status = await conn.fetchval("select status from slots where id = $1", old_slot)
        assert old_status == "blocked"


async def test_reminder_job_sends_each_stage_once(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        await make_booking(
            conn, student, await make_slot(conn, world.interviewer, hours_from_now(-25))
        )

        first = await reminders.run_result_reminders(conn)
        second = await reminders.run_result_reminders(conn)

        assert (first, second) == (3, 0)
        rows = await conn.fetch("select template from notifications order by template")
        assert [r["template"] for r in rows] == [
            "admin_result_overdue",
            "iv_result_reminder",
            "iv_result_reminder",
        ]


async def test_manual_reminder_goes_to_interviewer(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        booking_id = await make_booking(
            conn, student, await make_slot(conn, world.interviewer, hours_from_now(-3))
        )
        assert await admin_actions.remind_interviewer(conn, booking_id) is True
        owner = await conn.fetchval("select user_id from notifications")
        assert owner == world.interviewer.user_id
