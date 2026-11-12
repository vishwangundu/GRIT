"""AppError, the error catalogue, and the global handlers that format {"error": {...}}."""

import logging

import asyncpg
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

ERRORS: dict[str, tuple[int, str]] = {
    "unauthorized": (401, "Your session has expired. Sign in again."),
    "forbidden": (403, "You don't have access to this."),
    "not_eligible": (403, "You can't book an interview right now."),
    "slot_not_found": (404, "That slot doesn't exist."),
    "slot_taken": (409, "That slot was just taken. Pick another one."),
    "too_soon": (422, "Pick a slot at least 6 hours from now."),
    "too_far": (422, "Pick a slot within the next 14 days."),
    "reschedule_limit": (422, "You've used both reschedules for this interview."),
    "change_window_closed": (422, "Changes close 12 hours before your interview."),
    "badge_mismatch": (422, "That interviewer isn't cleared for this badge."),
    "no_booking": (404, "You don't have an interview booked."),
    "booking_not_found": (404, "Interview not found."),
    "booking_not_active": (409, "This booking is no longer active."),
    "not_your_interview": (403, "This interview belongs to another interviewer."),
    "interview_started": (422, "This interview has already started."),
    "interview_not_started": (422, "You can record a result once the interview starts."),
    "outcome_exists": (409, "A result is already recorded. Edit it instead."),
    "outcome_not_found": (404, "No result has been recorded for this interview."),
    "rubric_incomplete": (422, "Score all 4 rubric areas from 1 to 4."),
    "feedback_required": (
        422,
        "Feedback of at least 15 characters is required for Fail and Retake later.",
    ),
    "retake_date_invalid": (422, "Pick a retake date in the future."),
    "edit_window_closed": (403, "Results can only be edited within 2 hours of recording."),
    "edit_note_required": (422, "Admin edits need an audit note."),
    "journey_moved_on": (409, "The student's journey has moved on, so this result is locked."),
    "invalid_transition": (409, "That change isn't allowed from the current state."),
    "profile_not_found": (403, "No GRIT profile exists for this account."),
    "not_half_hour": (422, "Start and end must be on the hour or half hour."),
    "invalid_window": (422, "The end time must be after the start time."),
    "in_past": (422, "Pick a time in the future."),
    "beyond_horizon": (422, "You can add availability up to 14 days ahead."),
    "window_not_found": (404, "That availability window doesn't exist."),
    "window_has_bookings": (
        409,
        "This window has booked interviews. Cancel each one with a reason first.",
    ),
    "slot_not_changeable": (409, "Only open or blocked slots can be blocked or unblocked."),
    "student_not_found": (404, "Student not found."),
    "not_passed": (422, "Only a passed badge can be flagged."),
    "flag_not_found": (404, "Flag not found."),
    "flag_closed": (409, "This flag has already been decided."),
    "no_free_slot": (409, "That interviewer has no free slot at the same time."),
    "invalid_internal_key": (403, "Invalid service key."),
    "nudge_target_required": (422, "Pick students to nudge or a minimum days waiting."),
    "already_registered": (409, "This account is already registered. Sign in instead."),
    "invalid_campus": (422, "Pick a campus from the list."),
    "invalid_batch": (422, "Pick a batch from the list."),
}


class AppError(Exception):
    def __init__(self, code: str, http_status: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.http_status = http_status
        self.message = message


def app_error(code: str) -> AppError:
    """Build an AppError from the catalogue above."""
    http_status, message = ERRORS[code]
    return AppError(code, http_status, message)


def _body(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


async def _handle_app_error(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppError):
        raise exc
    logger.info("app_error", extra={"code": exc.code, "status": exc.http_status})
    return _body(exc.code, exc.message, exc.http_status)


async def _handle_validation(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc
    first = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(part) for part in first.get("loc", ()))
    message = f"{location}: {first.get('msg', 'Invalid request')}"
    return _body("validation_error", message, 422)


async def _handle_http(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        raise exc
    return _body(f"http_{exc.status_code}", str(exc.detail), exc.status_code)


async def _handle_unique(_: Request, __: Exception) -> JSONResponse:
    return _body("conflict", "This change conflicts with existing data.", 409)


async def _handle_exclusion(_: Request, __: Exception) -> JSONResponse:
    return _body("overlap", "This window overlaps one you already have.", 409)


async def _handle_check(_: Request, __: Exception) -> JSONResponse:
    return _body("constraint_violation", "This change breaks a data rule.", 422)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_validation)
    app.add_exception_handler(StarletteHTTPException, _handle_http)
    app.add_exception_handler(asyncpg.UniqueViolationError, _handle_unique)
    app.add_exception_handler(asyncpg.ExclusionViolationError, _handle_exclusion)
    app.add_exception_handler(asyncpg.CheckViolationError, _handle_check)
