"""Admin Users list: every profile with role and email; admins only."""

from collections.abc import AsyncIterator
from datetime import timedelta
from uuid import UUID

import asyncpg
import httpx
import jwt
import pytest

from app.core.clock import utc_now
from app.main import create_app
from tests.conftest import TEST_SIGNING_KEY
from tests.factories import World, make_student


def _auth(user_id: UUID) -> dict[str, str]:
    claims = {"sub": str(user_id), "aud": "authenticated", "exp": utc_now() + timedelta(hours=1)}
    return {"Authorization": f"Bearer {jwt.encode(claims, TEST_SIGNING_KEY, algorithm='HS256')}"}


@pytest.fixture
async def client(db: asyncpg.Pool) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app()
    app.state.pool = db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="https://test/api/v1") as c:
        yield c


async def test_admin_sees_every_user_with_email(
    client: httpx.AsyncClient, db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
    response = await client.get("/admin/users", headers=_auth(world.admin.user_id))
    assert response.status_code == 200
    body = response.json()
    assert body["counts"] == {"student": 1, "interviewer": 2, "admin": 1}
    assert body["users"][0]["role"] == "admin"
    row = next(u for u in body["users"] if u["id"] == str(student.actor.user_id))
    assert row["email"].endswith("@demo.grit")
    assert row["campus"] == "Hyderabad"
    assert row["miles"] == 2340


@pytest.mark.parametrize("who", ["student", "interviewer"])
async def test_only_admins_can_list_users(
    client: httpx.AsyncClient, db: asyncpg.Pool, world: World, who: str
) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
    user_id = student.actor.user_id if who == "student" else world.interviewer.user_id
    response = await client.get("/admin/users", headers=_auth(user_id))
    assert response.status_code == 403
