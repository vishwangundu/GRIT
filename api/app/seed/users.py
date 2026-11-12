"""Creates (or finds) auth users for the demo. Supabase Admin API when configured,
otherwise the local auth stub used in development and tests."""

from typing import Any, Protocol
from uuid import UUID

import httpx

from app.core.config import Settings
from app.db.session import Conn

_PAGE_SIZE = 1000


class Provisioner(Protocol):
    async def ensure(self, email: str) -> UUID: ...


class LocalProvisioner:
    def __init__(self, conn: Conn) -> None:
        self._conn = conn

    async def ensure(self, email: str) -> UUID:
        found = await self._conn.fetchval("select id from auth.users where email = $1", email)
        if found is None:
            found = await self._conn.fetchval(
                "insert into auth.users (id, email) values (gen_random_uuid(), $1) returning id",
                email,
            )
        return UUID(str(found))


class SupabaseProvisioner:
    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        if not settings.demo_user_password:
            raise RuntimeError("DEMO_USER_PASSWORD must be set to create demo users")
        key = settings.supabase_service_role_key
        self._client = client
        self._base = settings.supabase_url.rstrip("/") + "/auth/v1/admin/users"
        self._headers = {"apikey": key, "Authorization": f"Bearer {key}"}
        self._password = settings.demo_user_password
        self._known: dict[str, UUID] | None = None

    async def _load(self) -> dict[str, UUID]:
        if self._known is None:
            response = await self._client.get(
                self._base, headers=self._headers, params={"page": 1, "per_page": _PAGE_SIZE}
            )
            response.raise_for_status()
            users: list[dict[str, Any]] = response.json().get("users", [])
            self._known = {str(u["email"]).lower(): UUID(str(u["id"])) for u in users}
        return self._known

    async def ensure(self, email: str) -> UUID:
        known = await self._load()
        if email in known:
            return known[email]
        response = await self._client.post(
            self._base,
            headers=self._headers,
            json={"email": email, "password": self._password, "email_confirm": True},
        )
        response.raise_for_status()
        user_id = UUID(str(response.json()["id"]))
        known[email] = user_id
        return user_id
