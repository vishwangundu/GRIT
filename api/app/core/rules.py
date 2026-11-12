"""Business constants from the PRD. The only place these numbers may appear."""

from datetime import timedelta
from typing import Literal
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

JourneyState = Literal[
    "not_eligible",
    "eligible",
    "booked",
    "awaiting_result",
    "retake_later",
    "failed",
    "locked",
    "passed",
    "under_review",
    "nullified",
]
Role = Literal["student", "interviewer", "admin"]
ActorRole = Literal["student", "interviewer", "admin", "system"]
OutcomeResult = Literal["pass", "fail", "retake_later", "no_show"]
BookingStatus = Literal[
    "confirmed",
    "rescheduled",
    "cancelled_by_student",
    "cancelled_by_interviewer",
    "cancelled_by_system",
    "completed",
    "no_show",
]

# Booking (S1, S3, S4)
BOOK_MIN_LEAD = timedelta(hours=6)
BOOK_HORIZON = timedelta(days=14)
CHANGE_CUTOFF = timedelta(hours=12)
RESCHEDULE_MAX = 2
JOIN_OPENS_BEFORE = timedelta(minutes=10)

# Outcomes (I2, I3, section 3)
MAX_ATTEMPTS = 3
FAIL_COOLDOWN = timedelta(days=14)
NO_SHOW_COOLDOWN = timedelta(days=7)
OUTCOME_EDIT_WINDOW = timedelta(hours=2)
PASS_MILES = 500
FEEDBACK_MIN_CHARS = 15
RUBRIC_AREAS = ("problem_solving", "product_thinking", "code_walkthrough", "communication")
RUBRIC_MIN = 1
RUBRIC_MAX = 4

# Availability (I1, FR-I5)
SLOT_MINUTES = 30
AVAILABILITY_HORIZON = timedelta(days=14)

# Admin (A2, A3, section 9)
NUDGE_COOLDOWN = timedelta(hours=24)
SLOW_AFTER_DAYS = 7
RESULT_REMINDER_STAGES = (timedelta(hours=2), timedelta(hours=20))
RESULT_OVERDUE_AFTER = timedelta(hours=24)
SCHEDULER_INTERVAL = timedelta(minutes=60)
IDEMPOTENCY_TTL = timedelta(minutes=10)

# Student UI (FR-S1, FR-S5)
EVENTS_SHOWN = 6
LEADERBOARD_TOP = 20
DASHBOARD_POLL_SECONDS = 30
MORNING_ENDS_HOUR = 12
AFTERNOON_ENDS_HOUR = 17
RETAKE_DEFAULT_DAYS = 3

# Self-registration (students only). Campuses and batches also feed the sign-up form.
CAMPUSES = ("Hyderabad", "Pune", "Bengaluru", "Chennai")
BATCHES = ("2023", "2024", "2025")
