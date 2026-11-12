"""Interviewer schedule, interview detail and availability models."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.rules import OutcomeResult

Chip = Literal[
    "open",
    "upcoming",
    "live_now",
    "record_result",
    "result_overdue",
    "passed",
    "failed",
    "retake_later",
    "no_show",
    "blocked",
    "cancelled",
]
HHMM = r"^([01]\d|2[0-3]):[0-5]\d$"


class ScheduleItem(BaseModel):
    slot_id: UUID
    start_at: datetime
    end_at: datetime
    chip: Chip
    booking_id: UUID | None
    student_name: str | None
    badge_name: str | None


class ResultToRecord(BaseModel):
    booking_id: UUID
    student_name: str
    start_at: datetime
    is_overdue: bool


class ScheduleResponse(BaseModel):
    date: date
    items: list[ScheduleItem]
    to_record: list[ResultToRecord]


class StudentSummary(BaseModel):
    name: str
    campus: str
    batch: str


class SkillItem(BaseModel):
    name: str
    level: int


class AttemptItem(BaseModel):
    start_at: datetime
    result: OutcomeResult
    feedback_to_student: str
    recorded_at: datetime


class InterviewerOutcome(BaseModel):
    result: OutcomeResult
    rubric: dict[str, int] | None
    feedback_to_student: str
    internal_notes: str
    retake_after: datetime | None
    recorded_at: datetime
    editable_until: datetime
    can_edit: bool


class InterviewDetail(BaseModel):
    booking_id: UUID
    slot_id: UUID
    start_at: datetime
    end_at: datetime
    chip: Chip
    badge_name: str
    meeting_link: str | None
    join_opens_at: datetime
    is_join_open: bool
    can_cancel: bool
    can_record: bool
    student: StudentSummary
    skills: list[SkillItem]
    earlier_attempts: list[AttemptItem]
    outcome: InterviewerOutcome | None


class AvailabilitySlot(BaseModel):
    slot_id: UUID
    start_at: datetime
    end_at: datetime
    status: Literal["open", "booked", "blocked", "cancelled"]
    student_first_name: str | None
    booking_id: UUID | None


class AvailabilityWindow(BaseModel):
    window_id: UUID
    starts_at: datetime
    ends_at: datetime
    can_remove: bool
    slots: list[AvailabilitySlot]


class AvailabilityResponse(BaseModel):
    windows: list[AvailabilityWindow]


class WindowCreate(BaseModel):
    date: date
    start: str = Field(pattern=HHMM, description="IST, HH:MM on the hour or half hour")
    end: str = Field(pattern=HHMM, description="IST, HH:MM on the hour or half hour")


class WindowCreated(BaseModel):
    window_id: UUID
    slots_created: int


class SlotPatch(BaseModel):
    blocked: bool


class SlotPatched(BaseModel):
    slot_id: UUID
    status: Literal["open", "blocked"]


class Removed(BaseModel):
    removed: bool
