"""Interviewer availability routes (FR-I5)."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.db.session import Conn, get_conn
from app.deps.auth import Actor, require_role
from app.schemas.interviewer import (
    AvailabilityResponse,
    Removed,
    SlotPatch,
    SlotPatched,
    WindowCreate,
    WindowCreated,
)
from app.services import availability

router = APIRouter(prefix="/interviewer", tags=["availability"])
interviewer_only = require_role("interviewer")


@router.get("/availability")
async def list_availability(
    first: date | None = Query(default=None, alias="from"),
    last: date | None = Query(default=None, alias="to"),
    actor: Actor = Depends(interviewer_only),
    conn: Conn = Depends(get_conn),
) -> AvailabilityResponse:
    return await availability.list_windows(conn, actor, first, last)


@router.post("/availability", status_code=status.HTTP_201_CREATED)
async def add_window(
    body: WindowCreate, actor: Actor = Depends(interviewer_only), conn: Conn = Depends(get_conn)
) -> WindowCreated:
    return await availability.add_window(conn, actor, body)


@router.delete("/availability/{window_id}")
async def remove_window(
    window_id: UUID, actor: Actor = Depends(interviewer_only), conn: Conn = Depends(get_conn)
) -> Removed:
    return Removed(removed=await availability.remove_window(conn, actor, window_id))


@router.patch("/slots/{slot_id}")
async def block_slot(
    slot_id: UUID,
    body: SlotPatch,
    actor: Actor = Depends(interviewer_only),
    conn: Conn = Depends(get_conn),
) -> SlotPatched:
    new_status = await availability.set_blocked(conn, actor, slot_id, body.blocked)
    return SlotPatched(slot_id=slot_id, status="blocked" if new_status == "blocked" else "open")
