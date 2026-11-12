"""Admin Users list: every profile with its role and email."""

from app.db.session import Conn
from app.repositories import users
from app.schemas.admin import RoleCounts, UserRow, UsersResponse


async def list_users(conn: Conn) -> UsersResponse:
    rows = await users.list_all(conn)
    out = [
        UserRow(
            id=r.id,
            role=r.role,
            name=r.full_name,
            email=r.email,
            joined_at=r.created_at,
            campus=r.campus,
            batch=r.batch,
            miles=r.miles,
            badge_count=r.badge_count,
        )
        for r in rows
    ]
    counts = RoleCounts(
        student=sum(u.role == "student" for u in out),
        interviewer=sum(u.role == "interviewer" for u in out),
        admin=sum(u.role == "admin" for u in out),
    )
    return UsersResponse(counts=counts, users=out)
