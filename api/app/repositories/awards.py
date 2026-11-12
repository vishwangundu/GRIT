"""SQL for badge_awards and student Miles."""

from datetime import datetime
from uuid import UUID

from app.db.session import Conn
from app.repositories.rows import AwardRow


async def insert(conn: Conn, student_id: UUID, badge_id: int, outcome_id: UUID, miles: int) -> UUID:
    award_id = await conn.fetchval(
        """
        insert into badge_awards (student_id, badge_id, outcome_id, miles_awarded)
        values ($1, $2, $3, $4)
        returning id
        """,
        student_id,
        badge_id,
        outcome_id,
        miles,
    )
    return UUID(str(award_id))


async def live_for_outcome(conn: Conn, outcome_id: UUID) -> AwardRow | None:
    row = await conn.fetchrow(
        """
        select id, status, miles_awarded from badge_awards
        where outcome_id = $1 and status <> 'nullified'
        """,
        outcome_id,
    )
    return AwardRow.model_validate(dict(row)) if row else None


async def nullify(conn: Conn, award_id: UUID, at: datetime, reason: str) -> None:
    await conn.execute(
        """
        update badge_awards set status = 'nullified', nullified_at = $2, reason = $3
        where id = $1
        """,
        award_id,
        at,
        reason,
    )


async def get_miles(conn: Conn, student_id: UUID) -> int:
    miles = await conn.fetchval("select miles from students where id = $1", student_id)
    return int(miles or 0)


async def add_miles(conn: Conn, student_id: UUID, delta: int) -> None:
    await conn.execute("update students set miles = miles + $2 where id = $1", student_id, delta)
