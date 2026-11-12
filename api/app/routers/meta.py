"""GET /me and GET /rules."""

from fastapi import APIRouter, Depends, status

from app.core import rules
from app.db.session import Conn, get_conn
from app.deps.auth import Actor, Identity, current_actor, current_identity
from app.schemas.me import MeResponse
from app.schemas.meta import HealthResponse, RulesResponse
from app.schemas.register import RegisterRequest, RegistrationOptions
from app.services import profile, registration

router = APIRouter(tags=["meta"])
_HOUR = 3600


@router.get("/health")
async def health() -> HealthResponse:
    """Unauthenticated liveness check for the hosting platform."""
    return HealthResponse(status="ok")


@router.get("/registration-options")
async def registration_options() -> RegistrationOptions:
    """Public: campuses and batches for the sign-up form."""
    return registration.options()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    identity: Identity = Depends(current_identity),
    conn: Conn = Depends(get_conn),
) -> MeResponse:
    """Creates the student profile for a freshly signed-up Supabase user."""
    created = await registration.register_student(conn, identity, body)
    return MeResponse.model_validate(created.model_dump())


@router.get("/me")
async def me(actor: Actor = Depends(current_actor), conn: Conn = Depends(get_conn)) -> MeResponse:
    found = await profile.get_me(conn, actor)
    return MeResponse.model_validate(found.model_dump())


@router.get("/rules")
async def get_rules(_: Actor = Depends(current_actor)) -> RulesResponse:
    return RulesResponse(
        book_min_lead_hours=rules.BOOK_MIN_LEAD.total_seconds() / _HOUR,
        book_horizon_days=rules.BOOK_HORIZON.days,
        change_cutoff_hours=rules.CHANGE_CUTOFF.total_seconds() / _HOUR,
        reschedule_max=rules.RESCHEDULE_MAX,
        join_opens_minutes=int(rules.JOIN_OPENS_BEFORE.total_seconds() // 60),
        max_attempts=rules.MAX_ATTEMPTS,
        feedback_min_chars=rules.FEEDBACK_MIN_CHARS,
        rubric_areas=list(rules.RUBRIC_AREAS),
        rubric_min=rules.RUBRIC_MIN,
        rubric_max=rules.RUBRIC_MAX,
        outcome_edit_window_hours=rules.OUTCOME_EDIT_WINDOW.total_seconds() / _HOUR,
        slot_minutes=rules.SLOT_MINUTES,
        slow_after_days=rules.SLOW_AFTER_DAYS,
        dashboard_poll_seconds=rules.DASHBOARD_POLL_SECONDS,
        pass_miles=rules.PASS_MILES,
        retake_default_days=rules.RETAKE_DEFAULT_DAYS,
    )
