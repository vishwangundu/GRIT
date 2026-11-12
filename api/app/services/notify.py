"""Notification templates (PRD section 8) and the helper that stores them.

booked, pass and retake are the submitted student messages: their wording must not change.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.core.rules import IST
from app.db.session import Conn
from app.repositories import catalogue, notifications
from app.repositories.notifications import NotificationIn


@dataclass(frozen=True)
class Template:
    tone: str
    title: str
    body: str


TEMPLATES: dict[str, Template] = {
    "eligible": Template(
        "info",
        "You’re interview-ready",
        "You’ve cleared all {skill_count} skills for the {badge} Badge in {track}. "
        "Book a 30-minute interview to unlock it.",
    ),
    "booked": Template(
        "info",
        "Your interview is booked",
        "{track}, {badge} Badge. {date} · {start} – {end} IST · Online (Google Meet). "
        "Your join link appears on your dashboard 10 minutes before the start. "
        "Join from a laptop with your camera on, and keep your projects open to walk through. "
        "Plans changed? You can reschedule up to 2 times, until 12 hours before.",
    ),
    "pass": Template(
        "success",
        "{badge} Badge unlocked. You cleared the interview!",
        "+{miles} Miles have been added, and you are now on the Qualiflyer leaderboard. "
        "From your interviewer: “{feedback}”.",
    ),
    "retake": Template(
        "warning",
        "One more round needed for your {badge} interview",
        "This is not a fail, and it does not count against your attempts. "
        "Your interviewer needs another conversation to complete the assessment. "
        "What to prepare: “{feedback}”. You can book a new slot from {retake_date}.",
    ),
    "fail": Template(
        "danger",
        "You didn’t clear the {badge} interview this time",
        "From your interviewer: “{feedback}”. You can book again from {rebook_date}. "
        "You have {attempts_left} attempts left.",
    ),
    "no_show": Template(
        "danger",
        "You missed your interview",
        "We didn’t see you in the call at {start} on {date}. This counts as one attempt. "
        "You can book a new slot from {rebook_date}.",
    ),
    "locked": Template(
        "danger",
        "Your {badge} interview attempts are used up",
        "You’ve used all 3 attempts for this badge. The interview team will contact you "
        "within 3 working days about next steps.",
    ),
    "iv_cancelled": Template(
        "warning",
        "Your interview on {date} was cancelled",
        "Your interviewer can’t make it ({reason}). This doesn’t count as an attempt. "
        "Pick a new slot; you’ll be first in line when new slots open.",
    ),
    "nudge": Template(
        "info",
        "Your interview slot is waiting",
        "You became interview-ready {days} days ago. Book a slot this week to keep your spot "
        "on track for the December badge deadline.",
    ),
    "under_review": Template(
        "review",
        "Your {badge} Badge is under review",
        "We’ve received a report about a possible conduct issue in one of your GRIT "
        "assessments. Your badge stays on your profile while the interview team reviews it, "
        "usually within 5 working days. We’ll update you here.",
    ),
    "nullified": Template(
        "danger",
        "Your {badge} Badge has been withdrawn",
        "After review, the interview team found a breach of the NIAT code of conduct. "
        "The badge and its {miles} Miles have been removed. To appeal, reply to the GRIT team "
        "within 7 days.",
    ),
    "review_dismissed": Template(
        "success",
        "Your {badge} Badge is confirmed",
        "The review is complete and no issue was found. Your badge and Miles are unchanged.",
    ),
    "iv_result_reminder": Template(
        "warning",
        "Result due for {student}",
        "Your interview with {student} on {date} at {start} needs a result. "
        "Students see it within 24 hours.",
    ),
    "admin_result_overdue": Template(
        "danger",
        "Result overdue: {student}",
        "{interviewer} hasn’t recorded the result for {date}, {start}.",
    ),
}

# Second half of the pass body; only sent when a next badge exists in the track.
NEXT_BADGE_SENTENCE = (
    " Next stop: {next_badge} Badge. You have cleared {next_done} of its {next_total} skills."
)


def ist_date(moment: datetime) -> str:
    """Thu, 19 Nov"""
    local = moment.astimezone(IST)
    return f"{local:%a}, {local.day} {local:%b}"


def ist_time(moment: datetime) -> str:
    """4:30 PM"""
    local = moment.astimezone(IST)
    hour = int(f"{local:%I}")
    return f"{hour}:{local:%M} {local:%p}"


def badge_label(level: str) -> str:
    return level.replace("_", " ").title()


async def badge_vars(conn: Conn, badge_id: int, student_id: UUID) -> dict[str, str]:
    info = await catalogue.badge_info(conn, badge_id, student_id)
    values = {
        "badge": badge_label(info.badge_level),
        "track": info.track_name,
        "skill_count": str(info.skill_count),
    }
    if info.next_level:
        values |= {
            "next_badge": badge_label(info.next_level),
            "next_done": str(info.next_done),
            "next_total": str(info.next_total),
        }
    return values


def render(template: str, values: Mapping[str, str]) -> tuple[Template, str, str]:
    spec = TEMPLATES[template]
    body = spec.body
    if template == "pass" and "next_badge" in values:
        body += NEXT_BADGE_SENTENCE
    return spec, spec.title.format_map(values), body.format_map(values)


async def send(
    conn: Conn,
    user_id: UUID,
    template: str,
    values: Mapping[str, str],
    payload: dict[str, Any] | None = None,
) -> None:
    spec, title, body = render(template, values)
    await notifications.insert(
        conn,
        NotificationIn(
            user_id=user_id,
            template=template,
            title=title,
            body=body,
            tone=spec.tone,
            payload=payload or {},
        ),
    )
