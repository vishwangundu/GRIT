"""Leaderboard SQL over the v_leaderboard view (migration 007)."""

from uuid import UUID

from pydantic import BaseModel

from app.db.session import Conn


class RankedStudent(BaseModel):
    id: UUID
    full_name: str
    campus: str
    miles: int
    is_qualiflyer: bool
    is_paused: bool
    badge_count: int
    rank: int


async def standing(conn: Conn, student_id: UUID) -> RankedStudent | None:
    row = await conn.fetchrow(
        """
        select id, full_name, campus, miles, is_qualiflyer, is_paused, badge_count, rank
        from v_leaderboard where id = $1
        """,
        student_id,
    )
    return RankedStudent.model_validate(dict(row)) if row else None


async def tier_rows(
    conn: Conn, is_qualiflyer: bool, top: int, student_id: UUID
) -> list[RankedStudent]:
    rows = await conn.fetch(
        """
        select id, full_name, campus, miles, is_qualiflyer, is_paused, badge_count, rank
        from v_leaderboard
        where is_qualiflyer = $1 and (rank <= $2 or id = $3)
        order by rank, full_name
        """,
        is_qualiflyer,
        top,
        student_id,
    )
    return [RankedStudent.model_validate(dict(r)) for r in rows]
