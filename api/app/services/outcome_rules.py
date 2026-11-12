"""Pure rules for interview results: input validation and the effects of each result.
No I/O here, so every branch is cheap to unit test."""

from dataclasses import dataclass
from datetime import UTC, datetime, time
from typing import Any

from app.core.errors import app_error
from app.core.rules import (
    FAIL_COOLDOWN,
    FEEDBACK_MIN_CHARS,
    IST,
    MAX_ATTEMPTS,
    NO_SHOW_COOLDOWN,
    PASS_MILES,
    RUBRIC_AREAS,
    RUBRIC_MAX,
    RUBRIC_MIN,
    BookingStatus,
    JourneyState,
    OutcomeResult,
)
from app.repositories.outcomes import OutcomeFields
from app.repositories.rows import JourneyRow
from app.schemas.outcome import OutcomeCreate

# Stored journey states each result can leave behind; used to detect a journey that moved on.
RESULT_STATES: dict[OutcomeResult, frozenset[JourneyState]] = {
    "pass": frozenset({"passed"}),
    "retake_later": frozenset({"retake_later"}),
    "fail": frozenset({"failed", "locked"}),
    "no_show": frozenset({"failed", "locked"}),
}


@dataclass(frozen=True)
class Effect:
    journey: JourneyRow
    booking_status: BookingStatus
    template: str
    miles: int


def _rubric(data: OutcomeCreate) -> dict[str, int] | None:
    if data.result == "no_show":
        return None
    rubric = data.rubric or {}
    in_range = all(RUBRIC_MIN <= score <= RUBRIC_MAX for score in rubric.values())
    if set(rubric) != set(RUBRIC_AREAS) or not in_range:
        raise app_error("rubric_incomplete")
    return {area: rubric[area] for area in RUBRIC_AREAS}


def _retake_after(data: OutcomeCreate, now: datetime) -> datetime | None:
    if data.result != "retake_later":
        return None
    if data.retake_after is None:
        raise app_error("retake_date_invalid")
    at = datetime.combine(data.retake_after, time.min, tzinfo=IST).astimezone(UTC)
    if at <= now:
        raise app_error("retake_date_invalid")
    return at


def validate(data: OutcomeCreate, now: datetime) -> OutcomeFields:
    """FR-I3 validation. Raises rubric_incomplete, feedback_required or retake_date_invalid."""
    rubric = _rubric(data)
    feedback = data.feedback_to_student.strip()
    needs_feedback = data.result in ("fail", "retake_later")
    if needs_feedback and len(feedback) < FEEDBACK_MIN_CHARS:
        raise app_error("feedback_required")
    return OutcomeFields(
        result=data.result,
        rubric=rubric,
        feedback_to_student=feedback,
        internal_notes=data.internal_notes.strip(),
        retake_after=_retake_after(data, now),
        attempt_counted=data.result in ("fail", "no_show"),
    )


def _attempt_effect(journey: JourneyRow, result: OutcomeResult, now: datetime) -> Effect:
    attempts = journey.attempts_used + 1
    is_locked = attempts >= MAX_ATTEMPTS
    cooldown = FAIL_COOLDOWN if result == "fail" else NO_SHOW_COOLDOWN
    after = journey.model_copy(
        update={
            "state": "locked" if is_locked else "failed",
            "attempts_used": attempts,
            "next_bookable_at": None if is_locked else now + cooldown,
            "active_booking_id": None,
            "priority": False,
        }
    )
    template = "locked" if is_locked else ("fail" if result == "fail" else "no_show")
    status: BookingStatus = "no_show" if result == "no_show" else "completed"
    return Effect(journey=after, booking_status=status, template=template, miles=0)


def compute_effect(journey: JourneyRow, fields: OutcomeFields, now: datetime) -> Effect:
    """Section 3 side effects for a journey currently in awaiting_result."""
    if fields.result in ("fail", "no_show"):
        return _attempt_effect(journey, fields.result, now)
    is_pass = fields.result == "pass"
    after = journey.model_copy(
        update={
            "state": "passed" if is_pass else "retake_later",
            "next_bookable_at": None if is_pass else fields.retake_after,
            "active_booking_id": None,
            "priority": False,
        }
    )
    return Effect(
        journey=after,
        booking_status="completed",
        template="pass" if is_pass else "retake",
        miles=PASS_MILES if is_pass else 0,
    )


def snapshot(journey: JourneyRow, miles: int) -> dict[str, Any]:
    """prev_snapshot: the journey and Miles exactly as they were before the result."""
    return {
        "state": journey.state,
        "attempts_used": journey.attempts_used,
        "next_bookable_at": journey.next_bookable_at.isoformat()
        if journey.next_bookable_at
        else None,
        "priority": journey.priority,
        "active_booking_id": str(journey.active_booking_id) if journey.active_booking_id else None,
        "miles": miles,
    }


def restore(journey: JourneyRow, saved: dict[str, Any]) -> JourneyRow:
    fields = ("state", "attempts_used", "next_bookable_at", "priority", "active_booking_id")
    return JourneyRow.model_validate(journey.model_dump() | {name: saved[name] for name in fields})
