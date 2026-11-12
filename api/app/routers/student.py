"""Student routes. Thin: parse, call one service, return a schema."""

from fastapi import APIRouter, Depends, Header, Query, status

from app.db.session import Conn, get_conn
from app.deps.auth import Actor, require_role
from app.schemas.booking import BookedSlot, BookingCreate, BookingResponse, StateResponse
from app.schemas.dashboard import DashboardResponse
from app.schemas.student import (
    InboxResponse,
    LeaderboardResponse,
    MarkReadResponse,
    SlotsResponse,
    TierParam,
)
from app.services import booking, idempotency, inbox, leaderboard, student_dashboard, student_slots

router = APIRouter(prefix="/student", tags=["student"])
student_only = require_role("student")


@router.get("/dashboard")
async def dashboard(
    actor: Actor = Depends(student_only), conn: Conn = Depends(get_conn)
) -> DashboardResponse:
    return await student_dashboard.get_dashboard(conn, actor)


@router.get("/slots")
async def list_slots(
    actor: Actor = Depends(student_only), conn: Conn = Depends(get_conn)
) -> SlotsResponse:
    return await student_slots.list_slots(conn, actor)


@router.post("/bookings", status_code=status.HTTP_201_CREATED)
async def create_booking(
    body: BookingCreate,
    actor: Actor = Depends(student_only),
    conn: Conn = Depends(get_conn),
    idempotency_key: str | None = Header(default=None, max_length=200),
) -> BookingResponse:
    async def produce() -> BookingResponse:
        result = await booking.book_slot(conn, actor, body.slot_id)
        return BookingResponse(
            booking_id=result.booking_id,
            state=result.state,
            slot=BookedSlot(
                start_at=result.start_at,
                end_at=result.end_at,
                interviewer_name=result.interviewer_name,
            ),
            reschedules_left=result.reschedules_left,
            meeting_link=result.meeting_link,
        )

    scope_key = ("student_booking", idempotency_key)
    return await idempotency.run_once(conn, actor, scope_key, BookingResponse, produce)


@router.delete("/bookings/current")
async def cancel_current_booking(
    actor: Actor = Depends(student_only), conn: Conn = Depends(get_conn)
) -> StateResponse:
    return StateResponse(state=await booking.cancel_by_student(conn, actor))


@router.get("/notifications")
async def notifications(
    actor: Actor = Depends(student_only), conn: Conn = Depends(get_conn)
) -> InboxResponse:
    return await inbox.get_inbox(conn, actor)


@router.post("/notifications/read")
async def mark_read(
    actor: Actor = Depends(student_only), conn: Conn = Depends(get_conn)
) -> MarkReadResponse:
    return await inbox.mark_all_read(conn, actor)


@router.get("/leaderboard")
async def get_leaderboard(
    tier: TierParam = Query(default="pre"),
    actor: Actor = Depends(student_only),
    conn: Conn = Depends(get_conn),
) -> LeaderboardResponse:
    return await leaderboard.get_leaderboard(conn, actor, tier)
