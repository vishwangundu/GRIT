"""Slot picker, inbox and leaderboard responses for students."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

Period = Literal["morning", "afternoon", "evening"]
TierParam = Literal["qual", "pre"]


class SlotTime(BaseModel):
    slot_id: UUID
    start_at: datetime
    end_at: datetime
    period: Period


class SlotDay(BaseModel):
    date: date
    open_count: int
    times: list[SlotTime]


class CurrentSlot(BaseModel):
    start_at: datetime
    reschedules_left: int
    can_change: bool


class SlotsResponse(BaseModel):
    days: list[SlotDay]
    current_booking: CurrentSlot | None


class NotificationItem(BaseModel):
    id: UUID
    template: str
    title: str
    body: str
    tone: str
    created_at: datetime
    is_read: bool


class InboxResponse(BaseModel):
    items: list[NotificationItem]
    unread_count: int


class MarkReadResponse(BaseModel):
    marked: int


class LeaderboardRow(BaseModel):
    rank: int
    name: str
    campus: str
    miles: int
    is_me: bool
    is_paused: bool


class LeaderboardResponse(BaseModel):
    tier: TierParam
    rows: list[LeaderboardRow]
    my_tier: TierParam | None
    my_rank: int | None
