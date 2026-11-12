"""Interviewer schedule chips, detail panel and availability (FR-I1 to FR-I5)."""

from datetime import datetime, timedelta

import asyncpg
import pytest

from app.core.clock import utc_now
from app.core.errors import AppError
from app.core.rules import IST, BookingStatus, OutcomeResult
from app.schemas.interviewer import WindowCreate
from app.schemas.outcome import OutcomeCreate
from app.services import availability, interviewer_schedule, outcome
from app.services.interviewer_schedule import chip_for
from tests.factories import World, hours_from_now, make_booking, make_slot, make_student

NOW = utc_now()
START = NOW + timedelta(hours=1)
END = START + timedelta(minutes=30)


@pytest.mark.parametrize(
    ("now", "booking_status", "result", "chip"),
    [
        (NOW, None, None, "open"),
        (NOW, "confirmed", None, "upcoming"),
        (START + timedelta(minutes=5), "confirmed", None, "live_now"),
        (END + timedelta(hours=1), "confirmed", None, "record_result"),
        (END + timedelta(hours=25), "confirmed", None, "result_overdue"),
        (END, "completed", "pass", "passed"),
        (END, "no_show", "no_show", "no_show"),
    ],
)
def test_chip_for_each_slot_situation(
    now: datetime,
    booking_status: BookingStatus | None,
    result: OutcomeResult | None,
    chip: str,
) -> None:
    slot = (START, END, "booked" if booking_status else "open")
    assert chip_for(slot, booking_status, result, now) == chip


def test_blocked_and_cancelled_slots_keep_their_chip() -> None:
    assert chip_for((START, END, "blocked"), None, None, NOW) == "blocked"
    assert chip_for((START, END, "cancelled"), None, None, NOW) == "cancelled"


async def test_schedule_lists_day_and_results_to_record(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        await make_booking(
            conn, student, await make_slot(conn, world.interviewer, hours_from_now(-1))
        )

        today = utc_now().astimezone(IST).date()
        sched = await interviewer_schedule.get_schedule(conn, world.interviewer, today)

        assert len(sched.to_record) == 1
        assert sched.to_record[0].student_name == "Aarav Reddy"
        assert sched.to_record[0].is_overdue is False


async def test_detail_shows_internal_notes_and_edit_window(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        booking_id = await make_booking(
            conn, student, await make_slot(conn, world.interviewer, hours_from_now(-1))
        )
        rubric = {
            "problem_solving": 3,
            "product_thinking": 3,
            "code_walkthrough": 3,
            "communication": 3,
        }
        await outcome.record_outcome(
            conn,
            world.interviewer,
            booking_id,
            OutcomeCreate(result="pass", rubric=rubric, internal_notes="Strong."),
        )

        detail = await interviewer_schedule.get_interview(conn, world.interviewer, booking_id)

        assert detail.chip == "passed"
        assert detail.outcome is not None
        assert detail.outcome.internal_notes == "Strong."
        assert detail.outcome.can_edit is True
        assert detail.can_record is False
        assert detail.student.campus == "Hyderabad"
        assert "UI Engineering" in [s.name for s in detail.skills]


def _tomorrow_window(start: str, end: str) -> WindowCreate:
    day = (utc_now().astimezone(IST) + timedelta(days=1)).date()
    return WindowCreate(date=day, start=start, end=end)


async def test_add_window_creates_half_hour_slots(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        created = await availability.add_window(
            conn, world.interviewer, _tomorrow_window("18:00", "20:00")
        )
        assert created.slots_created == 4
        listed = await availability.list_windows(conn, world.interviewer, None, None)
        assert [len(w.slots) for w in listed.windows] == [4]


@pytest.mark.parametrize(
    ("start", "end", "code"),
    [("18:15", "19:00", "not_half_hour"), ("19:00", "18:00", "invalid_window")],
)
async def test_bad_window_is_rejected(
    db: asyncpg.Pool, world: World, start: str, end: str, code: str
) -> None:
    async with db.acquire() as conn:
        with pytest.raises(AppError) as err:
            await availability.add_window(conn, world.interviewer, _tomorrow_window(start, end))
        assert err.value.code == code


async def test_window_in_past_or_beyond_horizon_is_rejected(db: asyncpg.Pool, world: World) -> None:
    today = utc_now().astimezone(IST).date()
    async with db.acquire() as conn:
        with pytest.raises(AppError) as err:
            await availability.add_window(
                conn,
                world.interviewer,
                WindowCreate(date=today - timedelta(days=1), start="10:00", end="11:00"),
            )
        assert err.value.code == "in_past"
        with pytest.raises(AppError) as err:
            await availability.add_window(
                conn,
                world.interviewer,
                WindowCreate(date=today + timedelta(days=16), start="10:00", end="11:00"),
            )
        assert err.value.code == "beyond_horizon"


async def test_overlapping_window_violates_exclusion_constraint(
    db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        await availability.add_window(conn, world.interviewer, _tomorrow_window("18:00", "20:00"))
        with pytest.raises(asyncpg.ExclusionViolationError):
            await availability.add_window(
                conn, world.interviewer, _tomorrow_window("19:00", "21:00")
            )


async def test_window_with_booking_cannot_be_removed(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        created = await availability.add_window(
            conn, world.interviewer, _tomorrow_window("18:00", "19:00")
        )
        slot_id = await conn.fetchval(
            "select id from slots where window_id = $1 limit 1", created.window_id
        )
        await make_booking(conn, await make_student(conn, world), slot_id)
        with pytest.raises(AppError) as err:
            await availability.remove_window(conn, world.interviewer, created.window_id)
        assert err.value.code == "window_has_bookings"


async def test_removed_window_can_be_added_again(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        first = await availability.add_window(
            conn, world.interviewer, _tomorrow_window("18:00", "19:00")
        )
        await availability.remove_window(conn, world.interviewer, first.window_id)
        again = await availability.add_window(
            conn, world.interviewer, _tomorrow_window("18:00", "19:00")
        )
        assert again.slots_created == 2


async def test_removed_window_slots_leave_the_schedule(db: asyncpg.Pool, world: World) -> None:
    window = _tomorrow_window("18:00", "19:00")
    async with db.acquire() as conn:
        first = await availability.add_window(conn, world.interviewer, window)
        await availability.remove_window(conn, world.interviewer, first.window_id)
        sched = await interviewer_schedule.get_schedule(conn, world.interviewer, window.date)
        assert sched.items == []
        await availability.add_window(conn, world.interviewer, window)
        sched = await interviewer_schedule.get_schedule(conn, world.interviewer, window.date)
        assert [item.chip for item in sched.items] == ["open", "open"]


async def test_block_and_unblock_open_slot(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        slot_id = await make_slot(conn, world.interviewer, hours_from_now(30))
        assert await availability.set_blocked(conn, world.interviewer, slot_id, True) == "blocked"
        assert await availability.set_blocked(conn, world.interviewer, slot_id, False) == "open"
        await make_booking(conn, await make_student(conn, world), slot_id)
        with pytest.raises(AppError) as err:
            await availability.set_blocked(conn, world.interviewer, slot_id, True)
        assert err.value.code == "slot_not_changeable"
