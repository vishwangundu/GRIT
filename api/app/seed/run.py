"""Builds the full PRD section 11 demo. Used by scripts/seed.py and POST /internal/demo/reset."""

from datetime import datetime, timedelta
from uuid import UUID

from app.core.clock import utc_now
from app.core.rules import IST
from app.db.session import Conn
from app.deps.auth import Actor
from app.schemas.internal import ResetResponse
from app.seed import setup
from app.seed.data import (
    ADMIN,
    EXTRA_STUDENTS,
    INTERVIEWERS,
    NOVICE_CLEARED,
    SPECIALIST_HEAD_START,
    STUDENTS,
)
from app.seed.scenarios import Cast, apply_states
from app.seed.users import Provisioner
from app.services import eligibility

HORIZON_DAYS = 14
_WAITING_DAYS = {"aarav": 2, "tanvi": 12, "ananya": 9, "harsha": 4, "lakshmi": 1}
_DEFAULT_WAITING_DAYS = 5
_TANVI_NUDGED_DAYS_AGO = 3


async def _windows(conn: Conn, ids: dict[str, UUID], now_ist: datetime) -> int:
    today = now_ist.date()
    first_today = setup.floor_half_hour(now_ist) - timedelta(hours=2)
    created = await setup.window(conn, ids["priya"], first_today, first_today + timedelta(hours=3))
    for day in (today - timedelta(days=1), today - timedelta(days=2)):
        created += await setup.window(
            conn, ids["priya"], setup.ist_at(day, 10), setup.ist_at(day, 13)
        )
    for day in setup.upcoming_days(today, HORIZON_DAYS, skip_sunday=True):
        created += await setup.window(
            conn, ids["priya"], setup.ist_at(day, 10), setup.ist_at(day, 13)
        )
        created += await setup.window(
            conn, ids["rahul"], setup.ist_at(day, 14), setup.ist_at(day, 17)
        )
    for day in setup.upcoming_days(today, HORIZON_DAYS, skip_sunday=False)[::2]:
        created += await setup.window(
            conn, ids["neha"], setup.ist_at(day, 17), setup.ist_at(day, 20)
        )
    return created


async def _students(conn: Conn, users: Provisioner, cat: setup.Catalogue) -> dict[str, UUID]:
    ids: dict[str, UUID] = {}
    for index, person in enumerate(STUDENTS):
        student_id = await setup.student(conn, users, person, index)
        cleared = NOVICE_CLEARED[:3] if person.key == "lakshmi" else NOVICE_CLEARED
        await setup.clear_skills(conn, student_id, cat, (*cleared, *SPECIALIST_HEAD_START))
        await eligibility.recompute(conn, student_id)
        days = _WAITING_DAYS.get(person.key, _DEFAULT_WAITING_DAYS)
        await conn.execute(
            "update interview_journeys set eligible_at = $2 where student_id = $1 "
            "and eligible_at is not null",
            student_id,
            utc_now() - timedelta(days=days),
        )
        ids[person.key] = student_id
    for index, person in enumerate(EXTRA_STUDENTS):
        await setup.student(conn, users, person, index)
    return ids


async def seed_demo(conn: Conn, users: Provisioner) -> ResetResponse:
    # One clock reading for the whole seed: creating Supabase users can take over a minute,
    # and a second reading that crosses a half hour would look for slots that don't exist.
    now_ist = utc_now().astimezone(IST)
    first_today = setup.floor_half_hour(now_ist) - timedelta(hours=2)
    await setup.wipe(conn)
    cat = await setup.catalogue(conn)
    novice = cat.badge_ids["novice"]
    staff = {p.key: await setup.interviewer(conn, users, p, novice) for p in INTERVIEWERS}
    admin_id = await setup.profile(conn, users, ADMIN, "admin")
    slot_count = await _windows(conn, staff, now_ist)
    ids = await _students(conn, users, cat)
    cast = Cast(
        admin=Actor(user_id=admin_id, role="admin"),
        priya=Actor(user_id=staff["priya"], role="interviewer"),
        rahul=Actor(user_id=staff["rahul"], role="interviewer"),
        badge_id=novice,
    )
    days = (now_ist.date() - timedelta(days=1), now_ist.date() - timedelta(days=2), first_today)
    await apply_states(conn, cast, ids, days)
    await conn.execute(
        "update interview_journeys set last_nudged_at = $2 where student_id = $1",
        ids["tanvi"],
        utc_now() - timedelta(days=_TANVI_NUDGED_DAYS_AGO),
    )
    return ResetResponse(
        students=len(STUDENTS) + len(EXTRA_STUDENTS),
        interviewers=len(INTERVIEWERS),
        slots=slot_count,
    )
