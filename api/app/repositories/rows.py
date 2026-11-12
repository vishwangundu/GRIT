"""Typed views of database rows. Internal only; API responses use app/schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.core.rules import BookingStatus, JourneyState, OutcomeResult, Role


class JourneyRow(BaseModel):
    id: UUID
    student_id: UUID
    badge_id: int
    state: JourneyState
    attempts_used: int
    next_bookable_at: datetime | None
    active_booking_id: UUID | None
    priority: bool
    slot_start_at: datetime | None


class SlotRow(BaseModel):
    id: UUID
    interviewer_id: UUID
    start_at: datetime
    end_at: datetime
    status: str


class BookingRow(BaseModel):
    id: UUID
    journey_id: UUID
    slot_id: UUID
    student_id: UUID
    status: BookingStatus
    reschedule_count: int
    meeting_link: str | None


class BookingContext(BaseModel):
    """A booking joined with its slot and people, for interviewer actions."""

    booking_id: UUID
    booking_status: BookingStatus
    journey_id: UUID
    student_id: UUID
    student_name: str
    slot_id: UUID
    interviewer_id: UUID
    interviewer_name: str
    start_at: datetime
    end_at: datetime


class OutcomeRow(BaseModel):
    id: UUID
    booking_id: UUID
    journey_id: UUID
    interviewer_id: UUID
    result: OutcomeResult
    feedback_to_student: str
    attempt_counted: bool
    prev_snapshot: dict[str, Any]
    recorded_at: datetime
    locked_at: datetime


class AwardRow(BaseModel):
    id: UUID
    status: str
    miles_awarded: int


class Profile(BaseModel):
    id: UUID
    role: Role
    full_name: str
    email: str


class BadgeInfo(BaseModel):
    badge_level: str
    track_name: str
    skill_count: int
    next_level: str | None
    next_total: int
    next_done: int
