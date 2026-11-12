"""Seed the demo data (PRD section 11). Run from api/: `uv run python -m scripts.seed`.

Uses the Supabase Admin API to create users when SUPABASE_URL is set (needs
SUPABASE_SERVICE_ROLE_KEY and DEMO_USER_PASSWORD); otherwise the local auth stub.
"""

import asyncio
import logging

import asyncpg
import httpx

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.seed.run import seed_demo
from app.seed.users import LocalProvisioner, SupabaseProvisioner

logger = logging.getLogger("seed")


async def main() -> None:
    configure_logging()
    settings = get_settings()
    settings.require()
    conn = await asyncpg.connect(settings.database_url, statement_cache_size=0)
    try:
        async with conn.transaction():
            if settings.supabase_url:
                async with httpx.AsyncClient(timeout=30) as client:
                    result = await seed_demo(conn, SupabaseProvisioner(settings, client))
            else:
                result = await seed_demo(conn, LocalProvisioner(conn))
        logger.info("seeded", extra=result.model_dump())
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
