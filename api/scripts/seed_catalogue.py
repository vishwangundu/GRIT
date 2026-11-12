"""Add only the badge and skill catalogue, with no users, to a freshly migrated database.

Run from api/: `uv run python -m scripts.seed_catalogue`. Does nothing if badges exist.
"""

import asyncio
import logging

import asyncpg

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.seed import setup

logger = logging.getLogger("seed_catalogue")


async def main() -> None:
    configure_logging()
    settings = get_settings()
    settings.require()
    conn = await asyncpg.connect(settings.database_url, statement_cache_size=0)
    try:
        if await conn.fetchval("select count(*) from badges"):
            logger.info("catalogue already present, nothing added")
            return
        async with conn.transaction():
            cat = await setup.catalogue(conn)
        logger.info(
            "catalogue added",
            extra={"badges": len(cat.badge_ids), "skills": len(cat.skill_ids)},
        )
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
