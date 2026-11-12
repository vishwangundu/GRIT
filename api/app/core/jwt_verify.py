"""Supabase access-token verification: HS256 with the project JWT secret, or asymmetric
keys (ES256/RS256) from the project's JWKS endpoint, as PRD section 5 allows."""

import asyncio
from functools import lru_cache
from typing import Any

import jwt

from app.core.config import get_settings

_ASYMMETRIC = ["ES256", "RS256"]


@lru_cache
def _jwks_client(url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(url, cache_keys=True)


def _jwks_url() -> str:
    return get_settings().supabase_url.rstrip("/") + "/auth/v1/.well-known/jwks.json"


async def decode_token(token: str) -> dict[str, Any]:
    """Raises jwt.PyJWTError when the token is invalid, expired or for another audience."""
    settings = get_settings()
    algorithm = jwt.get_unverified_header(token).get("alg")
    if algorithm == "HS256" and settings.supabase_jwt_secret:
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience=settings.jwt_audience,
        )
    if not settings.supabase_url:
        raise jwt.InvalidTokenError("no verification key configured")
    client = _jwks_client(_jwks_url())
    signing_key = await asyncio.to_thread(client.get_signing_key_from_jwt, token)
    return jwt.decode(
        token, signing_key.key, algorithms=_ASYMMETRIC, audience=settings.jwt_audience
    )
