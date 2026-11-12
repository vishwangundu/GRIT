"""Seed building blocks: wipe, catalogue, people and availability windows."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from uuid import UUID

from app.core.rules import CAMPUSES, IST, SLOT_MINUTES
from app.db.session import Conn
from app.repositories import availability
from app.seed.data import (
    BADGE_LEVELS,
    REQUIREMENTS,
    SKILLS,
    TRACK,
    Person,
    email_for,
    meet_link_for,
)
from app.seed.users import Provisioner

DOMAIN_TABLES = (
    "idempotency_keys, notifications, journey_events, malpractice_flags, badge_awards, "
    "interview_outcomes, bookings, interview_journeys, slots, availability_windows, "
    "interviewer_badges, student_skill_levels, badge_skill_requirements, skills, badges, "
    "tracks, interviewers, students, profiles"
)
SUNDAY = 6
_STEP = timedelta(minutes=SLOT_MINUTES)


@dataclass(frozen=True)
class Catalogue:
    badge_ids: dict[str, int]
    skill_ids: list[int]


async def wipe(conn: Conn) -> None:
    await conn.execute("truncate " + DOMAIN_TABLES + " restart identity cascade")


async def catalogue(conn: Conn) -> Catalogue:
    track_id = await conn.fetchval("insert into tracks (name) values ($1) returning id", TRACK)
    badge_ids: dict[str, int] = {}
    for order, level in enumerate(BADGE_LEVELS, start=1):
        badge_ids[level] = int(
            await conn.fetchval(
                "insert into badges (track_id, level, level_order) values ($1, $2, $3) "
                "returning id",
                track_id,
                level,
                order,
            )
        )
    skill_ids = [
        int(await conn.fetchval("insert into skills (name) values ($1) returning id", name))
        for name in SKILLS
    ]
    for level, needs in REQUIREMENTS.items():
        for skill_index, min_level in needs:
            await conn.execute(
                "insert into badge_skill_requirements values ($1, $2, $3)",
                badge_ids[level],
                skill_ids[skill_index],
                min_level,
            )
    return Catalogue(badge_ids=badge_ids, skill_ids=skill_ids)


async def profile(conn: Conn, users: Provisioner, person: Person, role: str) -> UUID:
    email = email_for(person)
    user_id = await users.ensure(email)
    await conn.execute(
        "insert into profiles (id, role, full_name, email) values ($1, $2, $3, $4)",
        user_id,
        role,
        person.name,
        email,
    )
    return user_id


async def interviewer(conn: Conn, users: Provisioner, person: Person, badge_id: int) -> UUID:
    user_id = await profile(conn, users, person, "interviewer")
    await conn.execute(
        "insert into interviewers (id, campus, meet_link) values ($1, 'Hyderabad', $2)",
        user_id,
        meet_link_for(person),
    )
    await conn.execute("insert into interviewer_badges values ($1, $2)", user_id, badge_id)
    return user_id


async def student(conn: Conn, users: Provisioner, person: Person, index: int) -> UUID:
    user_id = await profile(conn, users, person, "student")
    await conn.execute(
        "insert into students (id, campus, batch, miles) values ($1, $2, '2025', $3)",
        user_id,
        CAMPUSES[index % len(CAMPUSES)],
        person.miles,
    )
    return user_id


async def clear_skills(
    conn: Conn, student_id: UUID, cat: Catalogue, cleared: Iterable[tuple[int, int]]
) -> None:
    for skill_index, level in cleared:
        for step in range(1, level + 1):
            await conn.execute(
                "insert into student_skill_levels (student_id, skill_id, level) "
                "values ($1, $2, $3)",
                student_id,
                cat.skill_ids[skill_index],
                step,
            )


def ist_at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=IST)


def floor_half_hour(moment: datetime) -> datetime:
    return moment.replace(
        minute=(moment.minute // SLOT_MINUTES) * SLOT_MINUTES, second=0, microsecond=0
    )


async def window(conn: Conn, interviewer_id: UUID, start: datetime, end: datetime) -> int:
    """Insert a window and its slots directly (seed may create past windows)."""
    window_id = await availability.insert_window(conn, interviewer_id, (start, end))
    created = 0
    current = start
    while current + _STEP <= end:
        created += int(
            await availability.insert_slot(
                conn, window_id, interviewer_id, (current, current + _STEP)
            )
        )
        current += _STEP
    return created


def upcoming_days(today: date, count: int, *, skip_sunday: bool) -> list[date]:
    days = [today + timedelta(days=offset) for offset in range(1, count + 1)]
    return [d for d in days if not (skip_sunday and d.weekday() == SUNDAY)]
