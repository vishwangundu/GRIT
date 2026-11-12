"""Interviewer schedule, interview detail, results and cancellation routes."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status

from app.db.session import Conn, get_conn
from app.deps.auth import Actor, require_role
from app.schemas.booking import InterviewerCancelRequest, InterviewerCancelResponse
from app.schemas.interviewer import InterviewDetail, ScheduleResponse
from app.schemas.outcome import OutcomeCreate, OutcomeEdit, OutcomeResponse
from app.services import booking, idempotency, interviewer_schedule, outcome
from app.services.outcome import RecordedOutcome

router = APIRouter(prefix="/interviewer", tags=["interviewer"])
interviewer_only = require_role("interviewer")
interviewer_or_admin = require_role("interviewer", "admin")


def _response(result: RecordedOutcome) -> OutcomeResponse:
    return OutcomeResponse(
        outcome_id=result.outcome_id,
        journey_state=result.journey_state,
        next_bookable_at=result.next_bookable_at,
        attempts_used=result.attempts_used,
        editable_until=result.editable_until,
    )


@router.get("/schedule")
async def schedule(
    day: date | None = Query(default=None, alias="date"),
    actor: Actor = Depends(interviewer_only),
    conn: Conn = Depends(get_conn),
) -> ScheduleResponse:
    return await interviewer_schedule.get_schedule(conn, actor, day)


@router.get("/interviews/{booking_id}")
async def interview_detail(
    booking_id: UUID,
    actor: Actor = Depends(interviewer_or_admin),
    conn: Conn = Depends(get_conn),
) -> InterviewDetail:
    return await interviewer_schedule.get_interview(conn, actor, booking_id)


@router.post("/interviews/{booking_id}/outcome", status_code=status.HTTP_201_CREATED)
async def record_outcome(
    booking_id: UUID,
    body: OutcomeCreate,
    actor: Actor = Depends(interviewer_only),
    conn: Conn = Depends(get_conn),
    idempotency_key: str | None = Header(default=None, max_length=200),
) -> OutcomeResponse:
    async def produce() -> OutcomeResponse:
        return _response(await outcome.record_outcome(conn, actor, booking_id, body))

    scope_key = (f"outcome:{booking_id}", idempotency_key)
    return await idempotency.run_once(conn, actor, scope_key, OutcomeResponse, produce)


@router.put("/interviews/{booking_id}/outcome")
async def edit_outcome(
    booking_id: UUID,
    body: OutcomeEdit,
    actor: Actor = Depends(interviewer_or_admin),
    conn: Conn = Depends(get_conn),
) -> OutcomeResponse:
    return _response(await outcome.edit_outcome(conn, actor, booking_id, body))


@router.post("/slots/{slot_id}/cancel")
async def cancel_slot(
    slot_id: UUID,
    body: InterviewerCancelRequest,
    actor: Actor = Depends(interviewer_or_admin),
    conn: Conn = Depends(get_conn),
) -> InterviewerCancelResponse:
    notified = await booking.cancel_by_interviewer(conn, actor, slot_id, body.reason)
    return InterviewerCancelResponse(student_notified=notified)
