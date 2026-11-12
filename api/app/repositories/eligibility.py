"""SQL for eligibility recompute: which badges a student qualifies for."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.db.session import Conn


class BadgeProgress(BaseModel):
    id: int
    level_order: int
    required: int
    met: int
    prev_passed: bool


async def badge_progress(conn: Conn, student_id: UUID) -> list[BadgeProgress]:
    rows = await conn.fetch(
        """
        select b.id, b.level_order,
          (select count(*) from badge_skill_requirements r where r.badge_id = b.id)::int
            as required,
          (select count(*) from badge_skill_requirements r
             where r.badge_id = b.id and exists (
               select 1 from student_skill_levels l
               where l.student_id = $1 and l.skill_id = r.skill_id
                 and l.status = 'cleared' and l.level >= r.min_level))::int as met,
          exists (select 1 from interview_journeys j join badges pb on pb.id = j.badge_id
                  where j.student_id = $1 and pb.track_id = b.track_id
                    and pb.level_order = b.level_order - 1
                    and j.state in ('passed', 'under_review')) as prev_passed
        from badges b
        order by b.track_id, b.level_order
        """,
        student_id,
    )
    return [BadgeProgress.model_validate(dict(r)) for r in rows]


async def ensure_journey(conn: Conn, student_id: UUID, badge_id: int) -> UUID:
    await conn.execute(
        """
        insert into interview_journeys (student_id, badge_id) values ($1, $2)
        on conflict (student_id, badge_id) do nothing
        """,
        student_id,
        badge_id,
    )
    found = await conn.fetchval(
        "select id from interview_journeys where student_id = $1 and badge_id = $2",
        student_id,
        badge_id,
    )
    return UUID(str(found))


async def set_eligible_at(conn: Conn, journey_id: UUID, at: datetime) -> None:
    await conn.execute(
        "update interview_journeys set eligible_at = $2 where id = $1", journey_id, at
    )


async def student_exists(conn: Conn, student_id: UUID) -> bool:
    return await conn.fetchval("select 1 from students where id = $1", student_id) is not None
