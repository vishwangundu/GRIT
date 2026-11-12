"""SQL for the hourly result-reminder job."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.db.session import Conn

REMINDER_LOCK_ID = 7_202_611


class MissingResult(BaseModel):
    booking_id: UUID
    interviewer_id: UUID
    interviewer_name: str
    student_name: str
    start_at: datetime
    end_at: datetime


async def try_job_lock(conn: Conn) -> bool:
    """Transaction-scoped advisory lock so two API instances never send the same reminder."""
    got = await conn.fetchval("select pg_try_advisory_xact_lock($1)", REMINDER_LOCK_ID)
    return bool(got)


async def missing_results(conn: Conn, ended_before: datetime) -> list[MissingResult]:
    rows = await conn.fetch(
        """
        select b.id as booking_id, s.interviewer_id, ip.full_name as interviewer_name,
               sp.full_name as student_name, s.start_at, s.end_at
        from bookings b
        join slots s on s.id = b.slot_id
        join profiles ip on ip.id = s.interviewer_id
        join profiles sp on sp.id = b.student_id
        where b.status = 'confirmed' and s.end_at <= $1
          and not exists (select 1 from interview_outcomes o where o.booking_id = b.id)
        order by s.end_at
        """,
        ended_before,
    )
    return [MissingResult.model_validate(dict(r)) for r in rows]
