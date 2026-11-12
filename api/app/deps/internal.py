"""Service-key check for /internal routes (called by the skills service, never by browsers)."""

import hmac

from fastapi import Header

from app.core.config import get_settings
from app.core.errors import app_error


async def require_internal_key(x_internal_key: str = Header(default="")) -> None:
    expected = get_settings().internal_api_key
    if not expected or not hmac.compare_digest(x_internal_key, expected):
        raise app_error("invalid_internal_key")
