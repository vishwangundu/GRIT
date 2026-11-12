"""Student dashboard, slot picker, inbox and leaderboard (FR-S1 to FR-S5)."""

from datetime import timedelta
from uuid import uuid4

import asyncpg

from app.core.rules import IST
from app.repositories.student_reads import OpenSlot
from app.services import booking, inbox, leaderboard, student_dashboard, student_slots
from app.services.student_slots import group_by_day, period_of
from tests.factories import MEET_LINK, World, hours_from_now, make_booking, make_slot, make_student


async def test_dashboard_for_booked_student_hides_link_until_join_opens(
    db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        await make_booking(
            conn, student, await make_slot(conn, world.interviewer, hours_from_now(24))
        )

        dash = await student_dashboard.get_dashboard(conn, student.actor)

        assert dash.journey is not None
        assert dash.journey.effective_state == "booked"
        assert dash.booking is not None
        assert dash.booking.interviewer_name == "Priya Sharma"
        assert dash.booking.can_change is True
        assert dash.booking.is_join_open is False
        assert dash.booking.meeting_link is None
        assert dash.stats.tier == "pre_qualiflyer"
        assert [r.status for r in dash.ladder] == ["current", "locked"]


async def test_dashboard_shows_link_ten_minutes_before_start(
    db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        await make_booking(
            conn, student, await make_slot(conn, world.interviewer, hours_from_now(0.1))
        )

        dash = await student_dashboard.get_dashboard(conn, student.actor)

        assert dash.booking is not None
        assert dash.booking.is_join_open is True
        assert dash.booking.meeting_link == MEET_LINK


async def test_slots_are_deduplicated_and_skip_too_soon(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        other = await conn.fetchval("select id from profiles where full_name = 'Neha Iyer'")
        await conn.execute("insert into interviewer_badges values ($1, $2)", other, world.badge_id)
        start = hours_from_now(30).replace(minute=0, second=0, microsecond=0)
        await make_slot(conn, world.interviewer, start)
        await make_slot(conn, world.uncleared_interviewer, start)
        await make_slot(conn, world.interviewer, hours_from_now(2))
        student = await make_student(conn, world)

        result = await student_slots.list_slots(conn, student.actor)

        times = [t for day in result.days for t in day.times]
        assert len(times) == 1
        assert times[0].start_at == start
        assert sum(day.open_count for day in result.days) == 1
        assert len(result.days) >= 14


def test_group_by_day_fills_empty_days_and_periods() -> None:
    morning = hours_from_now(0).astimezone(IST).replace(hour=9, minute=0) + timedelta(days=1)
    evening = morning.replace(hour=18)
    slots = [
        OpenSlot(id=uuid4(), start_at=s, end_at=s + timedelta(minutes=30))
        for s in (morning, evening)
    ]
    first = morning.date() - timedelta(days=1)
    days = group_by_day(slots, first, morning.date() + timedelta(days=1))
    assert [d.open_count for d in days] == [0, 2, 0]
    assert [period_of(t.start_at) for t in days[1].times] == ["morning", "evening"]


async def test_inbox_lists_newest_first_and_marks_read(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        await booking.book_slot(
            conn, student.actor, await make_slot(conn, world.interviewer, hours_from_now(24))
        )

        before = await inbox.get_inbox(conn, student.actor)
        marked = await inbox.mark_all_read(conn, student.actor)
        after = await inbox.get_inbox(conn, student.actor)

        assert before.unread_count == 1
        assert before.items[0].title == "Your interview is booked"
        assert marked.marked == 1
        assert after.unread_count == 0


async def test_leaderboard_ranks_by_miles_and_highlights_me(db: asyncpg.Pool, world: World) -> None:
    async with db.acquire() as conn:
        low = await make_student(conn, world, miles=1000)
        await make_student(conn, world, miles=3000)

        board = await leaderboard.get_leaderboard(conn, low.actor, "pre")

        assert [r.miles for r in board.rows] == [3000, 1000]
        assert [r.is_me for r in board.rows] == [False, True]
        assert (board.my_tier, board.my_rank) == ("pre", 2)
