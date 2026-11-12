"""Request/response models for booking, rescheduling and cancelling."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.rules import JourneyState


class BookingCreate(BaseModel):
    slot_id: UUID


class BookedSlot(BaseModel):
    start_at: datetime
    end_at: datetime
    interviewer_name: str


class BookingResponse(BaseModel):
    booking_id: UUID
    state: JourneyState
    slot: BookedSlot
    reschedules_left: int
    meeting_link: str | None


class StateResponse(BaseModel):
    state: JourneyState


class InterviewerCancelRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=200)


class InterviewerCancelResponse(BaseModel):
    student_notified: bool
