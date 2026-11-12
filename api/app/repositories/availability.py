"""SQL for availability windows and their slots."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.db.session import Conn


class WindowSlot(BaseModel):
    window_id: UUID
    window_starts_at: datetime
    window_ends_at: datetime
    slot_id: UUID | None
    start_at: datetime | None
    end_at: datetime | None
    status: str | None
    booking_id: UUID | None
    student_name: str | None


class WindowRef(BaseModel):
    id: UUID
    interviewer_id: UUID
    deleted_at: datetime | None


async def windows_with_slots(
    conn: Conn, interviewer_id: UUID, span: tuple[datetime, datetime]
) -> list[WindowSlot]:
    rows = await conn.fetch(
        """
        select w.id as window_id, w.starts_at as window_starts_at, w.ends_at as window_ends_at,
               s.id as slot_id, s.start_at, s.end_at, s.status,
               b.id as booking_id, p.full_name as student_name
        from availability_windows w
        left join slots s on s.window_id = w.id
        left join bookings b on b.slot_id = s.id and b.status = 'confirmed'
        left join profiles p on p.id = b.student_id
        where w.interviewer_id = $1 and w.deleted_at is null
          and w.ends_at > $2 and w.starts_at < $3
        order by w.starts_at, s.start_at
        """,
        interviewer_id,
        span[0],
        span[1],
    )
    return [WindowSlot.model_validate(dict(r)) for r in rows]


async def insert_window(conn: Conn, interviewer_id: UUID, span: tuple[datetime, datetime]) -> UUID:
    window_id = await conn.fetchval(
        """
        insert into availability_windows (interviewer_id, starts_at, ends_at)
        values ($1, $2, $3) returning id
        """,
        interviewer_id,
        span[0],
        span[1],
    )
    return UUID(str(window_id))


async def insert_slot(
    conn: Conn, window_id: UUID, interviewer_id: UUID, span: tuple[datetime, datetime]
) -> bool:
    """Create an open slot, or revive a cancelled one at the same time. False if skipped."""
    created = await conn.fetchval(
        """
        insert into slots (window_id, interviewer_id, start_at, end_at)
        values ($1, $2, $3, $4)
        on conflict (interviewer_id, start_at) do update
          set window_id = excluded.window_id, end_at = excluded.end_at,
              status = 'open', updated_at = now()
          where slots.status = 'cancelled'
        returning id
        """,
        window_id,
        interviewer_id,
        span[0],
        span[1],
    )
    return created is not None


async def get_window(conn: Conn, window_id: UUID) -> WindowRef | None:
    row = await conn.fetchrow(
        "select id, interviewer_id, deleted_at from availability_windows where id = $1 for update",
        window_id,
    )
    return WindowRef.model_validate(dict(row)) if row else None


async def confirmed_bookings_in_window(conn: Conn, window_id: UUID) -> int:
    count = await conn.fetchval(
        """
        select count(*) from bookings b join slots s on s.id = b.slot_id
        where s.window_id = $1 and b.status = 'confirmed'
        """,
        window_id,
    )
    return int(count or 0)


async def soft_delete_window(conn: Conn, window_id: UUID, at: datetime) -> None:
    await conn.execute(
        "update availability_windows set deleted_at = $2 where id = $1", window_id, at
    )
    await conn.execute(
        """
        update slots set status = 'cancelled', updated_at = now()
        where window_id = $1 and status in ('open', 'blocked')
        """,
        window_id,
    )


async def toggle_block(
    conn: Conn, slot_id: UUID, interviewer_id: UUID, change: tuple[str, str]
) -> bool:
    """Move a slot from change[0] to change[1]; False when it is not in change[0]."""
    updated = await conn.fetchval(
        """
        update slots set status = $4, updated_at = now()
        where id = $1 and interviewer_id = $2 and status = $3
        returning id
        """,
        slot_id,
        interviewer_id,
        change[0],
        change[1],
    )
    return updated is not None
