"""Read-only SQL for the admin Users list."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.rules import Role
from app.db.session import Conn


class UserRaw(BaseModel):
    id: UUID
    role: Role
    full_name: str
    email: str
    created_at: datetime
    campus: str | None
    batch: str | None
    miles: int | None
    badge_count: int


async def list_all(conn: Conn) -> list[UserRaw]:
    rows = await conn.fetch(
        """
        select p.id, p.role, p.full_name, p.email, p.created_at,
               coalesce(s.campus, i.campus) as campus, s.batch, s.miles,
               (select count(*) from badge_awards a
                 where a.student_id = p.id and a.status in ('active', 'under_review'))::int
                 as badge_count
        from profiles p
        left join students s on s.id = p.id
        left join interviewers i on i.id = p.id
        order by case p.role when 'admin' then 0 when 'interviewer' then 1 else 2 end,
                 p.full_name
        """
    )
    return [UserRaw.model_validate(dict(r)) for r in rows]
