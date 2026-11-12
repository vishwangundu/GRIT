"""Admin tracker and action models (FR-A1 to FR-A6, PRD section 7)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.core.rules import JourneyState, OutcomeResult

TrackerTab = Literal["notbooked", "booked", "awaiting", "results"]
WaitStatus = Literal[
    "not_booked", "can_rebook", "needs_rebooking", "retake_until", "cooldown_until"
]
AwaitStatus = Literal["in_progress", "due", "overdue"]


class TilesOut(BaseModel):
    not_booked: int
    booked: int
    awaiting: int
    awaiting_overdue: int
    results: int


class BadgeOptionOut(BaseModel):
    id: int
    name: str
    track: str


class NotBookedRow(BaseModel):
    student_id: UUID
    name: str
    campus: str
    effective_state: JourneyState
    status: WaitStatus
    until: datetime | None
    days_since_eligible: int | None
    is_slow: bool
    priority: bool
    last_nudged_at: datetime | None
    can_nudge: bool


class BookedRow(BaseModel):
    student_id: UUID
    booking_id: UUID
    slot_id: UUID
    name: str
    campus: str
    start_at: datetime
    interviewer_name: str
    booked_at: datetime
    reschedules_used: int


class AwaitingRow(BaseModel):
    student_id: UUID
    booking_id: UUID
    name: str
    campus: str
    start_at: datetime
    end_at: datetime
    interviewer_name: str
    status: AwaitStatus
    due_at: datetime


class ResultRow(BaseModel):
    student_id: UUID
    badge_id: int
    booking_id: UUID
    name: str
    campus: str
    result: OutcomeResult
    recorded_at: datetime
    interviewer_name: str
    award_status: str | None
    journey_state: JourneyState
    open_flag_id: UUID | None


class TrackerResponse(BaseModel):
    tab: TrackerTab
    badges: list[BadgeOptionOut]
    tiles: TilesOut
    not_booked_rows: list[NotBookedRow] = []
    booked_rows: list[BookedRow] = []
    awaiting_rows: list[AwaitingRow] = []
    result_rows: list[ResultRow] = []


class NudgeRequest(BaseModel):
    student_ids: list[UUID] | None = None
    min_days_waiting: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _one_target(self) -> "NudgeRequest":
        if not self.student_ids and self.min_days_waiting is None:
            raise ValueError("Pass student_ids or min_days_waiting")
        return self


class NudgeResponse(BaseModel):
    sent: int
    skipped_recent: int


class SentResponse(BaseModel):
    sent: bool


class ReassignRequest(BaseModel):
    interviewer_id: UUID


class ReassignOption(BaseModel):
    interviewer_id: UUID
    name: str


class ReassignOptions(BaseModel):
    options: list[ReassignOption]


class ReassignResponse(BaseModel):
    booking_id: UUID
    slot_id: UUID
    interviewer_name: str


class FlagCreate(BaseModel):
    student_id: UUID
    badge_id: int
    source: str = Field(min_length=3, max_length=200)
    evidence_url: str | None = Field(default=None, max_length=500)


class FlagCreated(BaseModel):
    flag_id: UUID
    journey_state: JourneyState


class FlagDecision(BaseModel):
    decision: Literal["uphold", "dismiss"]
    note: str = Field(min_length=3, max_length=1000)


class FlagDecided(BaseModel):
    flag_id: UUID
    journey_state: JourneyState
    award_status: str


class UserRow(BaseModel):
    id: UUID
    role: Literal["student", "interviewer", "admin"]
    name: str
    email: str
    joined_at: datetime
    campus: str | None
    batch: str | None
    miles: int | None
    badge_count: int


class RoleCounts(BaseModel):
    student: int
    interviewer: int
    admin: int


class UsersResponse(BaseModel):
    counts: RoleCounts
    users: list[UserRow]
