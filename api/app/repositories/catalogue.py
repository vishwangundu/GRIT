"""SQL for badge, track and skill-progress facts used in notification copy."""

from uuid import UUID

from app.db.session import Conn
from app.repositories.rows import BadgeInfo


async def badge_info(conn: Conn, badge_id: int, student_id: UUID) -> BadgeInfo:
    row = await conn.fetchrow(
        """
        with cur as (
          select b.id, b.level, b.level_order, b.track_id, t.name as track_name
          from badges b join tracks t on t.id = b.track_id
          where b.id = $1
        ),
        nxt as (
          select b.id, b.level from badges b, cur
          where b.track_id = cur.track_id and b.level_order = cur.level_order + 1
        )
        select cur.level as badge_level, cur.track_name,
          (select count(*) from badge_skill_requirements r where r.badge_id = cur.id)
            as skill_count,
          (select level from nxt) as next_level,
          (select count(*) from badge_skill_requirements r where r.badge_id = (select id from nxt))
            as next_total,
          (select count(*) from badge_skill_requirements r
             where r.badge_id = (select id from nxt)
               and exists (select 1 from student_skill_levels l
                           where l.student_id = $2 and l.skill_id = r.skill_id
                             and l.status = 'cleared' and l.level >= r.min_level))
            as next_done
        from cur
        """,
        badge_id,
        student_id,
    )
    if row is None:
        raise RuntimeError(f"badge {badge_id} not found")
    return BadgeInfo.model_validate(dict(row))
