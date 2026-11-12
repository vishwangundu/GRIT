"""Prepare a registered account for manual testing. Run from api/:

    uv run python -m scripts.test_account <email> admin|interviewer|eligible

Sign up at /register first (every new account is a student). `admin` and `interviewer`
change the role; `eligible` clears the Novice skills for a student so they can book.
"""

import argparse
import asyncio
import logging
from uuid import UUID

import asyncpg

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.rules import CAMPUSES
from app.db.session import Conn
from app.seed.data import NOVICE_CLEARED
from app.services import eligibility

logger = logging.getLogger("test_account")
ACTIONS = ("admin", "interviewer", "eligible")
TEST_MEET_ROOM = "https://meet.google.com/grit-test-room"


async def _make_staff(conn: Conn, user_id: UUID, role: str) -> None:
    await conn.execute("delete from students where id = $1", user_id)
    await conn.execute("update profiles set role = $2 where id = $1", user_id, role)
    if role != "interviewer":
        return
    await conn.execute(
        "insert into interviewers (id, campus, meet_link) values ($1, $2, $3) "
        "on conflict (id) do nothing",
        user_id,
        CAMPUSES[0],
        TEST_MEET_ROOM,
    )
    await conn.execute(
        "insert into interviewer_badges (interviewer_id, badge_id) "
        "select $1, id from badges where level_order = 1 on conflict do nothing",
        user_id,
    )


async def _make_eligible(conn: Conn, user_id: UUID) -> None:
    skill_ids = [row["id"] for row in await conn.fetch("select id from skills order by id")]
    for skill_index, level in NOVICE_CLEARED:
        await conn.execute(
            "insert into student_skill_levels (student_id, skill_id, level) "
            "values ($1, $2, $3) on conflict do nothing",
            user_id,
            skill_ids[skill_index],
            level,
        )
    await eligibility.recompute(conn, user_id)


async def run(email: str, action: str) -> None:
    settings = get_settings()
    settings.require()
    conn = await asyncpg.connect(settings.database_url, statement_cache_size=0)
    try:
        user_id = await conn.fetchval("select id from profiles where email = $1", email)
        if user_id is None:
            raise SystemExit(f"No account for {email}. Register it at /register first.")
        async with conn.transaction():
            if action == "eligible":
                await _make_eligible(conn, user_id)
            else:
                await _make_staff(conn, user_id, action)
        logger.info("account updated", extra={"action": action})
    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a registered account for testing.")
    parser.add_argument("email")
    parser.add_argument("action", choices=ACTIONS)
    args = parser.parse_args()
    configure_logging()
    asyncio.run(run(args.email.strip().lower(), args.action))


if __name__ == "__main__":
    main()
