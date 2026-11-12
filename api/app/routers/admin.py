"""Admin tracker and actions (FR-A1 to FR-A6). Outcome override uses the PUT outcome route."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.db.session import Conn, get_conn
from app.deps.auth import Actor, require_role
from app.schemas.admin import (
    FlagCreate,
    FlagCreated,
    FlagDecided,
    FlagDecision,
    NudgeRequest,
    NudgeResponse,
    ReassignOptions,
    ReassignRequest,
    ReassignResponse,
    SentResponse,
    TrackerResponse,
    TrackerTab,
)
from app.services import admin_actions, flags, tracker

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_role("admin")


@router.get("/tracker")
async def get_tracker(
    badge_id: int | None = Query(default=None),
    tab: TrackerTab = Query(default="notbooked"),
    _: Actor = Depends(admin_only),
    conn: Conn = Depends(get_conn),
) -> TrackerResponse:
    return await tracker.get_tracker(conn, badge_id, tab)


@router.post("/nudges")
async def nudge(
    body: NudgeRequest, _: Actor = Depends(admin_only), conn: Conn = Depends(get_conn)
) -> NudgeResponse:
    return await admin_actions.send_nudges(conn, body)


@router.post("/reminders/{booking_id}")
async def remind(
    booking_id: UUID, _: Actor = Depends(admin_only), conn: Conn = Depends(get_conn)
) -> SentResponse:
    return SentResponse(sent=await admin_actions.remind_interviewer(conn, booking_id))


@router.get("/bookings/{booking_id}/reassign-options")
async def reassign_options(
    booking_id: UUID, _: Actor = Depends(admin_only), conn: Conn = Depends(get_conn)
) -> ReassignOptions:
    return await admin_actions.reassign_options(conn, booking_id)


@router.post("/bookings/{booking_id}/reassign")
async def reassign(
    booking_id: UUID,
    body: ReassignRequest,
    actor: Actor = Depends(admin_only),
    conn: Conn = Depends(get_conn),
) -> ReassignResponse:
    return await admin_actions.reassign(conn, actor, booking_id, body.interviewer_id)


@router.post("/flags")
async def raise_flag(
    body: FlagCreate, actor: Actor = Depends(admin_only), conn: Conn = Depends(get_conn)
) -> FlagCreated:
    return await flags.raise_flag(conn, actor, body)


@router.post("/flags/{flag_id}/decision")
async def decide_flag(
    flag_id: UUID,
    body: FlagDecision,
    actor: Actor = Depends(admin_only),
    conn: Conn = Depends(get_conn),
) -> FlagDecided:
    return await flags.decide_flag(conn, actor, flag_id, body)
