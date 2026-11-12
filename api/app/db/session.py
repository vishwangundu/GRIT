"""asyncpg pool lifecycle and the per-request connection dependency."""

from collections.abc import AsyncIterator
from typing import TypeAlias

import asyncpg
from asyncpg.pool import PoolConnectionProxy
from fastapi import Request

Conn: TypeAlias = "asyncpg.Connection[asyncpg.Record] | PoolConnectionProxy[asyncpg.Record]"
Pool: TypeAlias = "asyncpg.Pool[asyncpg.Record]"


async def create_pool(dsn: str) -> Pool:
    # statement_cache_size=0 keeps us compatible with Supabase's transaction pooler.
    return await asyncpg.create_pool(dsn, min_size=1, max_size=10, statement_cache_size=0)


async def get_conn(request: Request) -> AsyncIterator[Conn]:
    pool: Pool = request.app.state.pool
    async with pool.acquire() as conn:
        yield conn
