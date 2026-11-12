"""Student self-registration. The role is never taken from the client: sign-up always
creates a student. Interviewers and admins are provisioned by the interview team."""

from app.core.errors import app_error
from app.core.rules import BATCHES, CAMPUSES
from app.db.session import Conn
from app.deps.auth import Identity
from app.repositories import profiles
from app.repositories.rows import Profile
from app.schemas.register import RegisterRequest, RegistrationOptions
from app.services import eligibility


def options() -> RegistrationOptions:
    return RegistrationOptions(campuses=list(CAMPUSES), batches=list(BATCHES))


async def register_student(conn: Conn, identity: Identity, body: RegisterRequest) -> Profile:
    if body.campus not in CAMPUSES:
        raise app_error("invalid_campus")
    if body.batch not in BATCHES:
        raise app_error("invalid_batch")
    async with conn.transaction():
        if await profiles.get(conn, identity.user_id) is not None:
            raise app_error("already_registered")
        details = (body.full_name.strip(), body.campus, body.batch)
        await profiles.create_student(conn, identity.user_id, identity.email.lower(), details)
        await eligibility.recompute(conn, identity.user_id)
    profile = await profiles.get(conn, identity.user_id)
    if profile is None:
        raise app_error("profile_not_found")
    return profile
