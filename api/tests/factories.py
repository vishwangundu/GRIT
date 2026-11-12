"""Direct-SQL builders for test data. They bypass services on purpose, so tests can start
from any state (e.g. a booking whose slot has already started)."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import asyncpg

from app.core.clock import utc_now
from app.deps.auth import Actor

MEET_LINK = "https://meet.google.com/abc-defg-hij"


@dataclass(frozen=True)
class World:
    badge_id: int
    interviewer: Actor
    uncleared_interviewer: Actor
    admin: Actor


@dataclass(frozen=True)
class StudentRef:
    actor: Actor
    journey_id: UUID


async def make_user(conn: asyncpg.Connection, role: str, name: str) -> UUID:
    user_id = uuid4()
    email = f"{user_id.hex[:8]}@demo.grit"
    await conn.execute("insert into auth.users (id, email) values ($1, $2)", user_id, email)
    await conn.execute(
        "insert into profiles (id, role, full_name, email) values ($1, $2, $3, $4)",
        user_id,
        role,
        name,
        email,
    )
    return user_id


async def _catalogue(conn: asyncpg.Connection) -> int:
    track = await conn.fetchval(
        "insert into tracks (name) values ('AI Product Mastery') returning id"
    )
    novice = await conn.fetchval(
        "insert into badges (track_id, level, level_order) values ($1, 'novice', 1) returning id",
        track,
    )
    specialist = await conn.fetchval(
        "insert into badges (track_id, level, level_order) values ($1, 'specialist', 2) "
        "returning id",
        track,
    )
    for index, (name, level) in enumerate(
        [
            ("Computational Thinking", 1),
            ("CS Fundamentals", 1),
            ("Applied Gen AI Development", 1),
            ("UI Engineering", 2),
        ],
        start=1,
    ):
        await conn.execute("insert into skills (id, name) values ($1, $2)", index, name)
        await conn.execute(
            "insert into badge_skill_requirements values ($1, $2, $3)", novice, index, level
        )
    await conn.execute("insert into skills (id, name) values (5, 'Product Thinking'), (6, 'APIs')")
    await conn.execute(
        "insert into badge_skill_requirements values ($1, 5, 1), ($1, 6, 1)", specialist
    )
    return int(novice)


async def make_interviewer(conn: asyncpg.Connection, name: str, badge_id: int | None) -> Actor:
    user_id = await make_user(conn, "interviewer", name)
    await conn.execute(
        "insert into interviewers (id, meet_link) values ($1, $2)", user_id, MEET_LINK
    )
    if badge_id is not None:
        await conn.execute("insert into interviewer_badges values ($1, $2)", user_id, badge_id)
    return Actor(user_id=user_id, role="interviewer")


async def make_world(conn: asyncpg.Connection) -> World:
    badge_id = await _catalogue(conn)
    return World(
        badge_id=badge_id,
        interviewer=await make_interviewer(conn, "Priya Sharma", badge_id),
        uncleared_interviewer=await make_interviewer(conn, "Neha Iyer", None),
        admin=Actor(user_id=await make_user(conn, "admin", "Interview Team"), role="admin"),
    )


async def make_student(
    conn: asyncpg.Connection, world: World, state: str = "eligible", **journey: Any
) -> StudentRef:
    user_id = await make_user(conn, "student", "Aarav Reddy")
    await conn.execute(
        "insert into students (id, campus, batch, miles) values ($1, 'Hyderabad', '2025', $2)",
        user_id,
        journey.pop("miles", 2340),
    )
    await conn.execute(
        "insert into student_skill_levels (student_id, skill_id, level) "
        "values ($1, 1, 1), ($1, 2, 1), ($1, 3, 1), ($1, 4, 2), ($1, 5, 1)",
        user_id,
    )
    journey_id = await conn.fetchval(
        """
        insert into interview_journeys
          (student_id, badge_id, state, eligible_at, attempts_used, next_bookable_at, priority)
        values ($1, $2, $3, now() - interval '2 days', $4, $5, $6)
        returning id
        """,
        user_id,
        world.badge_id,
        state,
        journey.get("attempts_used", 0),
        journey.get("next_bookable_at"),
        journey.get("priority", False),
    )
    return StudentRef(actor=Actor(user_id=user_id, role="student"), journey_id=journey_id)


async def make_slot(
    conn: asyncpg.Connection, interviewer: Actor, start: datetime, status: str = "open"
) -> UUID:
    end = start + timedelta(minutes=30)
    window_id = await conn.fetchval(
        "insert into availability_windows (interviewer_id, starts_at, ends_at) "
        "values ($1, $2, $3) returning id",
        interviewer.user_id,
        start,
        end,
    )
    slot_id: UUID = await conn.fetchval(
        "insert into slots (window_id, interviewer_id, start_at, end_at, status) "
        "values ($1, $2, $3, $4, $5) returning id",
        window_id,
        interviewer.user_id,
        start,
        end,
        status,
    )
    return slot_id


async def make_booking(
    conn: asyncpg.Connection, student: StudentRef, slot_id: UUID, reschedule_count: int = 0
) -> UUID:
    booking_id: UUID = await conn.fetchval(
        "insert into bookings (journey_id, slot_id, student_id, reschedule_count, meeting_link) "
        "values ($1, $2, $3, $4, $5) returning id",
        student.journey_id,
        slot_id,
        student.actor.user_id,
        reschedule_count,
        MEET_LINK,
    )
    await conn.execute("update slots set status = 'booked' where id = $1", slot_id)
    await conn.execute(
        "update interview_journeys set state = 'booked', active_booking_id = $2 where id = $1",
        student.journey_id,
        booking_id,
    )
    return booking_id


def hours_from_now(hours: float) -> datetime:
    return utc_now() + timedelta(hours=hours)
