"""Request/response models for recording and editing interview results."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.rules import JourneyState, OutcomeResult


class OutcomeCreate(BaseModel):
    result: OutcomeResult
    rubric: dict[str, int] | None = None
    feedback_to_student: str = Field(default="", max_length=2000)
    internal_notes: str = Field(default="", max_length=2000)
    retake_after: date | None = Field(
        default=None, description="IST calendar date; the student can rebook from 00:00 IST."
    )


class OutcomeEdit(OutcomeCreate):
    edit_note: str | None = Field(
        default=None, max_length=1000, description="Required for admin edits."
    )


class OutcomeResponse(BaseModel):
    outcome_id: UUID
    journey_state: JourneyState
    next_bookable_at: datetime | None
    attempts_used: int
    editable_until: datetime
