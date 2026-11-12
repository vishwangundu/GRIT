"""SQL for bookings."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.rules import BookingStatus
from app.db.session import Conn
from app.repositories.rows import BookingContext, BookingRow

_SELECT = """
select id, journey_id, slot_id, student_id, status, reschedule_count, meeting_link
from bookings
"""


@dataclass(frozen=True)
class BookingIn:
    journey_id: UUID
    slot_id: UUID
    student_id: UUID
    reschedule_count: int
    meeting_link: str | None


@dataclass(frozen=True)
class Cancellation:
    by: UUID
    at: datetime
    reason: str | None


async def insert(conn: Conn, booking: BookingIn) -> UUID:
    booking_id = await conn.fetchval(
        """
        insert into bookings (journey_id, slot_id, student_id, reschedule_count, meeting_link)
        values ($1, $2, $3, $4, $5)
        returning id
        """,
        booking.journey_id,
        booking.slot_id,
        booking.student_id,
        booking.reschedule_count,
        booking.meeting_link,
    )
    return UUID(str(booking_id))


async def get(conn: Conn, booking_id: UUID) -> BookingRow | None:
    row = await conn.fetchrow(_SELECT + " where id = $1", booking_id)
    return BookingRow.model_validate(dict(row)) if row else None


async def confirmed_for_slot(conn: Conn, slot_id: UUID) -> BookingRow | None:
    row = await conn.fetchrow(_SELECT + " where slot_id = $1 and status = 'confirmed'", slot_id)
    return BookingRow.model_validate(dict(row)) if row else None


async def set_status(conn: Conn, booking_id: UUID, status: BookingStatus) -> None:
    await conn.execute("update bookings set status = $2 where id = $1", booking_id, status)


async def cancel(
    conn: Conn, booking_id: UUID, status: BookingStatus, cancellation: Cancellation
) -> None:
    await conn.execute(
        """
        update bookings
        set status = $2, cancelled_by = $3, cancelled_at = $4, cancel_reason = $5
        where id = $1
        """,
        booking_id,
        status,
        cancellation.by,
        cancellation.at,
        cancellation.reason,
    )


async def get_context(conn: Conn, booking_id: UUID) -> BookingContext | None:
    row = await conn.fetchrow(
        """
        select b.id as booking_id, b.status as booking_status, b.journey_id, b.student_id,
               sp.full_name as student_name, s.id as slot_id, s.interviewer_id,
               ip.full_name as interviewer_name, s.start_at, s.end_at
        from bookings b
        join slots s on s.id = b.slot_id
        join profiles sp on sp.id = b.student_id
        join profiles ip on ip.id = s.interviewer_id
        where b.id = $1
        """,
        booking_id,
    )
    return BookingContext.model_validate(dict(row)) if row else None
