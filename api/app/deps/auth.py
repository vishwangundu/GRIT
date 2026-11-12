"""Supabase JWT verification and role checks. The role always comes from profiles."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from uuid import UUID

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import app_error
from app.core.jwt_verify import decode_token
from app.core.rules import Role
from app.db.session import Conn, get_conn
from app.repositories import profiles

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Actor:
    user_id: UUID
    role: Role


@dataclass(frozen=True)
class Identity:
    """A verified Supabase user who may not have a GRIT profile yet (sign-up)."""

    user_id: UUID
    email: str


async def _decode_identity(token: str) -> Identity:
    try:
        claims = await decode_token(token)
        return Identity(user_id=UUID(str(claims["sub"])), email=str(claims.get("email") or ""))
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise app_error("unauthorized") from exc


async def current_identity(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Identity:
    if creds is None:
        raise app_error("unauthorized")
    identity = await _decode_identity(creds.credentials)
    if not identity.email:
        raise app_error("unauthorized")
    return identity


async def current_actor(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    conn: Conn = Depends(get_conn),
) -> Actor:
    if creds is None:
        raise app_error("unauthorized")
    user_id = (await _decode_identity(creds.credentials)).user_id
    request.state.user_id = user_id
    role = await profiles.get_role(conn, user_id)
    if role is None:
        raise app_error("profile_not_found")
    return Actor(user_id=user_id, role=role)


def require_role(*roles: Role) -> Callable[..., Awaitable[Actor]]:
    async def _check(actor: Actor = Depends(current_actor)) -> Actor:
        if actor.role not in roles:
            raise app_error("forbidden")
        return actor

    return _check
