"""Service-key endpoints: eligibility recompute and demo reset."""

from uuid import UUID

from pydantic import BaseModel

from app.core.rules import JourneyState


class RecomputeRequest(BaseModel):
    student_id: UUID


class JourneyStateOut(BaseModel):
    badge_id: int
    state: JourneyState


class RecomputeResponse(BaseModel):
    student_id: UUID
    journeys: list[JourneyStateOut]


class ResetResponse(BaseModel):
    students: int
    interviewers: int
    slots: int
