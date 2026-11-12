"""Builds GET /student/dashboard from the effective-state view (PRD FR-S1)."""

from collections.abc import Mapping
from datetime import datetime
from uuid import UUID

from app.core.clock import utc_now
from app.core.errors import app_error
from app.core.rules import (
    CHANGE_CUTOFF,
    EVENTS_SHOWN,
    JOIN_OPENS_BEFORE,
    MAX_ATTEMPTS,
    RESCHEDULE_MAX,
)
from app.db.session import Conn
from app.deps.auth import Actor
from app.repositories import leaderboard, notifications, profiles, slots, student_reads
from app.repositories.student_reads import JourneyView, LadderSkill
from app.schemas.dashboard import (
    BadgeRef,
    BookingView,
    DashboardResponse,
    EventItem,
    JourneyCard,
    LadderRung,
    LadderSkillView,
    OutcomeView,
    RungStatus,
    Stats,
)
from app.services.notify import badge_label

_RUNG_FROM_STATE: dict[str, RungStatus] = {
    "passed": "earned",
    "under_review": "under_review",
    "nullified": "withdrawn",
}


def primary_journey(journeys: list[JourneyView]) -> JourneyView | None:
    """The journey the card is about: the lowest badge not yet passed, else the highest."""
    for journey in journeys:
        if journey.state != "passed":
            return journey
    return journeys[-1] if journeys else None


def _card(journey: JourneyView) -> JourneyCard:
    return JourneyCard(
        id=journey.id,
        badge=BadgeRef(
            id=journey.badge_id,
            name=badge_label(journey.badge_level),
            track=journey.track_name,
            level_order=journey.level_order,
        ),
        state=journey.state,
        effective_state=journey.effective_state,
        priority=journey.priority,
        attempts_used=journey.attempts_used,
        attempts_left=MAX_ATTEMPTS - journey.attempts_used,
        next_bookable_at=journey.next_bookable_at,
        eligible_at=journey.eligible_at,
    )


async def _booking(conn: Conn, journey: JourneyView, now: datetime) -> BookingView | None:
    if journey.effective_state not in ("booked", "awaiting_result") or journey.start_at is None:
        return None
    if journey.booking_id is None or journey.end_at is None or journey.interviewer_id is None:
        return None
    name, _ = await slots.interviewer_details(conn, journey.interviewer_id)
    join_opens_at = journey.start_at - JOIN_OPENS_BEFORE
    is_join_open = join_opens_at <= now < journey.end_at
    return BookingView(
        booking_id=journey.booking_id,
        start_at=journey.start_at,
        end_at=journey.end_at,
        interviewer_name=name,
        reschedules_left=RESCHEDULE_MAX - (journey.reschedule_count or 0),
        can_change=journey.effective_state == "booked" and journey.start_at - now >= CHANGE_CUTOFF,
        join_opens_at=join_opens_at,
        is_join_open=is_join_open,
        meeting_link=journey.meeting_link if is_join_open else None,
    )


def build_ladder(skills: list[LadderSkill], journeys: list[JourneyView]) -> list[LadderRung]:
    states = {j.badge_id: j.state for j in journeys}
    rungs: dict[int, LadderRung] = {}
    for row in skills:
        rung = rungs.setdefault(
            row.badge_id,
            LadderRung(
                badge_id=row.badge_id,
                name=badge_label(row.level),
                level_order=row.level_order,
                status="locked",
                skills_done=0,
                skills_total=0,
                skills=[],
            ),
        )
        if row.skill_name is not None and row.min_level is not None:
            rung.skills.append(
                LadderSkillView(name=row.skill_name, min_level=row.min_level, cleared=row.cleared)
            )
            rung.skills_total += 1
            rung.skills_done += int(row.cleared)
    ordered = sorted(rungs.values(), key=lambda r: r.level_order)
    _assign_statuses(ordered, states)
    return ordered


def _assign_statuses(rungs: list[LadderRung], states: Mapping[int, str]) -> None:
    has_open_rung = False
    for rung in rungs:
        state = states.get(rung.badge_id)
        if state is not None:
            rung.status = _RUNG_FROM_STATE.get(state, "current")
        elif not has_open_rung:
            rung.status = "next"
        has_open_rung = has_open_rung or rung.status in ("current", "next", "withdrawn")


async def _stats(conn: Conn, student_id: UUID) -> Stats:
    standing = await leaderboard.standing(conn, student_id)
    if standing is None:
        raise app_error("student_not_found")
    return Stats(
        miles=standing.miles,
        tier="qualiflyer" if standing.is_qualiflyer else "pre_qualiflyer",
        rank=standing.rank,
        badge_count=standing.badge_count,
    )


async def get_dashboard(conn: Conn, actor: Actor) -> DashboardResponse:
    now = utc_now()
    profile = await profiles.get(conn, actor.user_id)
    campus = await conn.fetchval("select campus from students where id = $1", actor.user_id)
    if profile is None or campus is None:
        raise app_error("student_not_found")
    journeys = await student_reads.journeys(conn, actor.user_id)
    journey = primary_journey(journeys)
    response = DashboardResponse(
        name=profile.full_name,
        campus=str(campus),
        stats=await _stats(conn, actor.user_id),
        journey=None,
        booking=None,
        last_outcome=None,
        ladder=[],
        events=[],
        unread_count=await notifications.unread_count(conn, actor.user_id),
    )
    if journey is None:
        return response
    outcome = await student_reads.last_outcome(conn, journey.id)
    events = await student_reads.recent_events(conn, journey.id, EVENTS_SHOWN)
    skills = await student_reads.ladder(conn, journey.track_id, actor.user_id)
    return response.model_copy(
        update={
            "journey": _card(journey),
            "booking": await _booking(conn, journey, now),
            "last_outcome": OutcomeView.model_validate(outcome.model_dump()) if outcome else None,
            "ladder": build_ladder(skills, journeys),
            "events": [EventItem.model_validate(e.model_dump()) for e in events],
        }
    )
