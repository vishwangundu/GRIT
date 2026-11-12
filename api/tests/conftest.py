"""Test fixtures. Needs TEST_DATABASE_URL pointing at a throwaway Postgres database:
the suite drops and recreates the public and auth schemas there."""

import os
from collections.abc import AsyncIterator
from pathlib import Path

import asyncpg
import pytest

TEST_SIGNING_KEY = "local-test-signing-key-not-a-real-credential"
os.environ["SUPABASE_JWT_SECRET"] = TEST_SIGNING_KEY
os.environ.setdefault("DATABASE_URL", os.environ.get("TEST_DATABASE_URL", ""))

from app.core.config import get_settings  # noqa: E402
from tests.factories import World, make_world  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SQL_FILES = [
    ROOT / "db/local/000_supabase_auth_stub.sql",
    *sorted((ROOT / "db/migrations").glob("*.sql")),
]
TABLES = (
    "idempotency_keys, notifications, journey_events, malpractice_flags, badge_awards, "
    "interview_outcomes, "
    "bookings, interview_journeys, slots, availability_windows, interviewer_badges, "
    "student_skill_levels, badge_skill_requirements, skills, badges, tracks, interviewers, "
    "students, profiles, auth.users"
)

get_settings.cache_clear()


@pytest.fixture(scope="session")
async def pool() -> AsyncIterator[asyncpg.Pool]:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")
    conn = await asyncpg.connect(url)
    await conn.execute(
        "drop schema if exists public cascade; drop schema if exists auth cascade; "
        "create schema public;"
    )
    for sql_file in SQL_FILES:
        await conn.execute(sql_file.read_text())
    await conn.close()
    created = await asyncpg.create_pool(url, min_size=2, max_size=10)
    yield created
    await created.close()


@pytest.fixture
async def db(pool: asyncpg.Pool) -> asyncpg.Pool:
    async with pool.acquire() as conn:
        await conn.execute("truncate " + TABLES + " restart identity cascade")
    return pool


@pytest.fixture
async def world(db: asyncpg.Pool) -> World:
    async with db.acquire() as conn:
        return await make_world(conn)
