"""HTTP layer: JWT auth, role checks, status codes and the error shape."""

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
from tests.factories import World, hours_from_now, make_slot, make_student


def _auth(user_id: UUID, signing_key: str = TEST_SIGNING_KEY) -> dict[str, str]:
    claims = {"sub": str(user_id), "aud": "authenticated", "exp": utc_now() + timedelta(hours=1)}
    return {"Authorization": f"Bearer {jwt.encode(claims, signing_key, algorithm='HS256')}"}


@pytest.fixture
async def client(db: asyncpg.Pool) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app()
    app.state.pool = db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="https://test/api/v1") as c:
        yield c


async def test_missing_token_returns_401_error_shape(client: httpx.AsyncClient) -> None:
    response = await client.get("/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


async def test_token_signed_with_wrong_key_returns_401(
    client: httpx.AsyncClient, world: World
) -> None:
    response = await client.get(
        "/me", headers=_auth(world.admin.user_id, "a-different-signing-key-of-32-bytes!!")
    )
    assert response.status_code == 401


async def test_me_returns_role_from_profiles(client: httpx.AsyncClient, world: World) -> None:
    response = await client.get("/me", headers=_auth(world.interviewer.user_id))
    assert response.status_code == 200
    assert response.json()["role"] == "interviewer"
    assert response.json()["full_name"] == "Priya Sharma"


async def test_student_cannot_call_interviewer_routes(
    client: httpx.AsyncClient, db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
    response = await client.post(
        "/interviewer/slots/00000000-0000-0000-0000-000000000000/cancel",
        json={"reason": "illness"},
        headers=_auth(student.actor.user_id),
    )
    assert response.status_code == 403
    assert response.json() == {
        "error": {"code": "forbidden", "message": "You don't have access to this."}
    }


async def test_booking_returns_201_with_prd_shape(
    client: httpx.AsyncClient, db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        slot_id = await make_slot(conn, world.interviewer, hours_from_now(24))

    response = await client.post(
        "/student/bookings", json={"slot_id": str(slot_id)}, headers=_auth(student.actor.user_id)
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"booking_id", "state", "slot", "reschedules_left", "meeting_link"}
    assert body["state"] == "booked"
    assert body["slot"]["interviewer_name"] == "Priya Sharma"
    assert body["slot"]["start_at"].endswith("Z") or body["slot"]["start_at"].endswith("+00:00")


async def test_taken_slot_returns_409_with_prd_message(
    client: httpx.AsyncClient, db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        first = await make_student(conn, world)
        second = await make_student(conn, world)
        slot_id = await make_slot(conn, world.interviewer, hours_from_now(24))
    payload = {"slot_id": str(slot_id)}
    await client.post("/student/bookings", json=payload, headers=_auth(first.actor.user_id))

    response = await client.post(
        "/student/bookings", json=payload, headers=_auth(second.actor.user_id)
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {"code": "slot_taken", "message": "That slot was just taken. Pick another one."}
    }


async def test_invalid_body_uses_error_shape(client: httpx.AsyncClient, world: World) -> None:
    response = await client.post(
        "/interviewer/slots/00000000-0000-0000-0000-000000000000/cancel",
        json={},
        headers=_auth(world.interviewer.user_id),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_repeated_idempotency_key_returns_first_response(
    client: httpx.AsyncClient, db: asyncpg.Pool, world: World
) -> None:
    async with db.acquire() as conn:
        student = await make_student(conn, world)
        slot_id = await make_slot(conn, world.interviewer, hours_from_now(24))
    headers = {**_auth(student.actor.user_id), "Idempotency-Key": "tap-1"}
    payload = {"slot_id": str(slot_id)}

    first = await client.post("/student/bookings", json=payload, headers=headers)
    second = await client.post("/student/bookings", json=payload, headers=headers)

    assert (first.status_code, second.status_code) == (201, 201)
    assert first.json() == second.json()


async def test_internal_routes_need_service_key(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/internal/eligibility/recompute",
        json={"student_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "invalid_internal_key"


async def test_rules_endpoint_exposes_constants(client: httpx.AsyncClient, world: World) -> None:
    response = await client.get("/rules", headers=_auth(world.admin.user_id))
    assert response.status_code == 200
    assert response.json()["reschedule_max"] == 2


async def test_health_needs_no_token(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")
    assert (response.status_code, response.json()) == (200, {"status": "ok"})


async def test_asymmetric_token_without_jwks_config_is_rejected(
    client: httpx.AsyncClient, world: World
) -> None:
    token = jwt.encode({"sub": str(world.admin.user_id)}, "k" * 48, algorithm="HS384")
    response = await client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
