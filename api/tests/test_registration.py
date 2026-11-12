"""Student self-registration: role is always student, profile created once."""

from collections.abc import AsyncIterator
from datetime import timedelta
from uuid import UUID, uuid4

import asyncpg
import httpx
import jwt
import pytest

from app.core.clock import utc_now
from app.main import create_app
from tests.conftest import TEST_SIGNING_KEY

BODY = {"full_name": "Riya Kapoor", "campus": "Pune", "batch": "2025"}


def _token(user_id: UUID, email: str | None) -> dict[str, str]:
    claims: dict[str, object] = {
        "sub": str(user_id),
        "aud": "authenticated",
        "exp": utc_now() + timedelta(hours=1),
    }
    if email is not None:
        claims["email"] = email
    return {"Authorization": f"Bearer {jwt.encode(claims, TEST_SIGNING_KEY, algorithm='HS256')}"}


@pytest.fixture
async def client(db: asyncpg.Pool) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app()
    app.state.pool = db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="https://test/api/v1") as c:
        yield c


async def _auth_user(db: asyncpg.Pool, email: str) -> UUID:
    user_id = uuid4()
    async with db.acquire() as conn:
        await conn.execute("insert into auth.users (id, email) values ($1, $2)", user_id, email)
    return user_id


async def test_registration_options_are_public(client: httpx.AsyncClient) -> None:
    response = await client.get("/registration-options")
    assert response.status_code == 200
    assert "Pune" in response.json()["campuses"]
    assert response.json()["batches"] == ["2023", "2024", "2025"]


@pytest.mark.usefixtures("world")
async def test_signup_creates_student_profile_and_journey(
    client: httpx.AsyncClient, db: asyncpg.Pool
) -> None:
    user_id = await _auth_user(db, "riya@demo.grit")

    response = await client.post("/register", json=BODY, headers=_token(user_id, "Riya@Demo.grit"))

    assert response.status_code == 201
    assert response.json() == {
        "id": str(user_id),
        "role": "student",
        "full_name": "Riya Kapoor",
        "email": "riya@demo.grit",
    }
    async with db.acquire() as conn:
        state = await conn.fetchval(
            "select state from interview_journeys where student_id = $1", user_id
        )
        miles = await conn.fetchval("select miles from students where id = $1", user_id)
    assert (state, miles) == ("not_eligible", 0)
    me = await client.get("/me", headers=_token(user_id, "riya@demo.grit"))
    assert me.json()["role"] == "student"


async def test_role_in_body_is_ignored(client: httpx.AsyncClient, db: asyncpg.Pool) -> None:
    user_id = await _auth_user(db, "sneaky@demo.grit")
    response = await client.post(
        "/register", json={**BODY, "role": "admin"}, headers=_token(user_id, "sneaky@demo.grit")
    )
    assert response.status_code == 201
    assert response.json()["role"] == "student"


async def test_second_registration_returns_409(client: httpx.AsyncClient, db: asyncpg.Pool) -> None:
    user_id = await _auth_user(db, "twice@demo.grit")
    headers = _token(user_id, "twice@demo.grit")
    await client.post("/register", json=BODY, headers=headers)
    again = await client.post("/register", json=BODY, headers=headers)
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "already_registered"


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [("campus", "Atlantis", "invalid_campus"), ("batch", "1999", "invalid_batch")],
)
async def test_unknown_campus_or_batch_is_rejected(
    client: httpx.AsyncClient, db: asyncpg.Pool, field: str, value: str, code: str
) -> None:
    user_id = await _auth_user(db, f"{code}@demo.grit")
    response = await client.post(
        "/register", json={**BODY, field: value}, headers=_token(user_id, f"{code}@demo.grit")
    )
    assert (response.status_code, response.json()["error"]["code"]) == (422, code)


async def test_token_without_email_cannot_register(
    client: httpx.AsyncClient, db: asyncpg.Pool
) -> None:
    user_id = await _auth_user(db, "noemail@demo.grit")
    response = await client.post("/register", json=BODY, headers=_token(user_id, None))
    assert response.status_code == 401
