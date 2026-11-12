"""SQL for slots and interviewer facts needed when booking."""

from uuid import UUID

from app.db.session import Conn
from app.repositories.rows import SlotRow


async def get(conn: Conn, slot_id: UUID) -> SlotRow | None:
    row = await conn.fetchrow(
        "select id, interviewer_id, start_at, end_at, status from slots where id = $1", slot_id
    )
    return SlotRow.model_validate(dict(row)) if row else None


async def claim_open(conn: Conn, slot_id: UUID) -> bool:
    """Atomically move an open slot to booked. False means someone else got it first."""
    claimed = await conn.fetchval(
        """
        update slots set status = 'booked', updated_at = now()
        where id = $1 and status = 'open'
        returning id
        """,
        slot_id,
    )
    return claimed is not None


async def set_status(conn: Conn, slot_id: UUID, status: str) -> None:
    await conn.execute(
        "update slots set status = $2, updated_at = now() where id = $1", slot_id, status
    )


async def interviewer_has_badge(conn: Conn, interviewer_id: UUID, badge_id: int) -> bool:
    found = await conn.fetchval(
        """
        select 1 from interviewer_badges ib
        join interviewers i on i.id = ib.interviewer_id
        where ib.interviewer_id = $1 and ib.badge_id = $2 and i.active
        """,
        interviewer_id,
        badge_id,
    )
    return found is not None


async def interviewer_details(conn: Conn, interviewer_id: UUID) -> tuple[str, str | None]:
    row = await conn.fetchrow(
        """
        select p.full_name, i.meet_link
        from interviewers i join profiles p on p.id = i.id
        where i.id = $1
        """,
        interviewer_id,
    )
    if row is None:
        return ("", None)
    link = row["meet_link"]
    return (str(row["full_name"]), str(link) if link is not None else None)
