"""GET /rules: business constants the frontend needs, so they are never hard-coded twice."""

from pydantic import BaseModel


class RulesResponse(BaseModel):
    book_min_lead_hours: float
    book_horizon_days: int
    change_cutoff_hours: float
    reschedule_max: int
    join_opens_minutes: int
    max_attempts: int
    feedback_min_chars: int
    rubric_areas: list[str]
    rubric_min: int
    rubric_max: int
    outcome_edit_window_hours: float
    slot_minutes: int
    slow_after_days: int
    dashboard_poll_seconds: int
    pass_miles: int
    retake_default_days: int


class HealthResponse(BaseModel):
    status: str
