"""GET /student/dashboard response. Never carries internal notes or other students' data."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.core.rules import JourneyState, OutcomeResult

Tier = Literal["qualiflyer", "pre_qualiflyer"]
RungStatus = Literal["earned", "current", "under_review", "withdrawn", "next", "locked"]


class BadgeRef(BaseModel):
    id: int
    name: str
    track: str
    level_order: int


class Stats(BaseModel):
    miles: int
    tier: Tier
    rank: int | None
    badge_count: int


class JourneyCard(BaseModel):
    id: UUID
    badge: BadgeRef
    state: JourneyState
    effective_state: JourneyState
    priority: bool
    attempts_used: int
    attempts_left: int
    next_bookable_at: datetime | None
    eligible_at: datetime | None


class BookingView(BaseModel):
    booking_id: UUID
    start_at: datetime
    end_at: datetime
    interviewer_name: str
    reschedules_left: int
    can_change: bool
    join_opens_at: datetime
    is_join_open: bool
    meeting_link: str | None


class OutcomeView(BaseModel):
    result: OutcomeResult
    feedback_to_student: str
    rubric: dict[str, int] | None
    recorded_at: datetime
    retake_after: datetime | None


class LadderSkillView(BaseModel):
    name: str
    min_level: int
    cleared: bool


class LadderRung(BaseModel):
    badge_id: int
    name: str
    level_order: int
    status: RungStatus
    skills_done: int
    skills_total: int
    skills: list[LadderSkillView]


class EventItem(BaseModel):
    from_state: str | None
    to_state: str
    reason: str | None
    created_at: datetime


class DashboardResponse(BaseModel):
    name: str
    campus: str
    stats: Stats
    journey: JourneyCard | None
    booking: BookingView | None
    last_outcome: OutcomeView | None
    ladder: list[LadderRung]
    events: list[EventItem]
    unread_count: int
