"""Profile lookups for GET /me."""

from app.core.errors import app_error
from app.db.session import Conn
from app.deps.auth import Actor
from app.repositories import profiles
from app.repositories.rows import Profile


async def get_me(conn: Conn, actor: Actor) -> Profile:
    profile = await profiles.get(conn, actor.user_id)
    if profile is None:
        raise app_error("profile_not_found")
    return profile
