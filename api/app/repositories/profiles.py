"""SQL for profiles."""

from uuid import UUID

from app.core.rules import Role
from app.db.session import Conn
from app.repositories.rows import Profile

_ROLES: dict[str, Role] = {"student": "student", "interviewer": "interviewer", "admin": "admin"}


async def get_role(conn: Conn, user_id: UUID) -> Role | None:
    value = await conn.fetchval("select role from profiles where id = $1", user_id)
    return _ROLES.get(str(value)) if value is not None else None


async def get(conn: Conn, user_id: UUID) -> Profile | None:
    row = await conn.fetchrow(
        "select id, role, full_name, email from profiles where id = $1", user_id
    )
    return Profile.model_validate(dict(row)) if row else None


async def create_student(
    conn: Conn, user_id: UUID, email: str, details: tuple[str, str, str]
) -> None:
    """details = (full_name, campus, batch). Role is always student for self-registration."""
    full_name, campus, batch = details
    await conn.execute(
        "insert into profiles (id, role, full_name, email) values ($1, 'student', $2, $3)",
        user_id,
        full_name,
        email,
    )
    await conn.execute(
        "insert into students (id, campus, batch) values ($1, $2, $3)", user_id, campus, batch
    )
