"""The journey state machine: effective state, allowed transitions, audited writes."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.errors import app_error
from app.core.rules import ActorRole, JourneyState
from app.db.session import Conn
from app.deps.auth import Actor
from app.repositories import journeys
from app.repositories.journeys import EventIn
from app.repositories.rows import JourneyRow

# Stored-state transitions from PRD section 3. The "-> awaiting_result" moves out of a result
# state exist only to undo an outcome during an edit (I3, FR-A6).
TRANSITIONS: dict[JourneyState, frozenset[JourneyState]] = {
    "not_eligible": frozenset({"eligible"}),
    "eligible": frozenset({"booked", "not_eligible"}),
    "booked": frozenset({"booked", "eligible", "not_eligible", "awaiting_result"}),
    "awaiting_result": frozenset({"passed", "retake_later", "failed", "locked"}),
    "retake_later": frozenset({"eligible", "awaiting_result"}),
    "failed": frozenset({"eligible", "awaiting_result"}),
    "locked": frozenset({"awaiting_result"}),
    "passed": frozenset({"under_review", "awaiting_result"}),
    "under_review": frozenset({"passed", "nullified"}),
    "nullified": frozenset(),
}


@dataclass(frozen=True)
class Audit:
    """Who caused a transition and why. actor=None means the system."""

    actor: Actor | None
    reason: str
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def role(self) -> ActorRole:
        return self.actor.role if self.actor else "system"


def effective_state(journey: JourneyRow, now: datetime) -> JourneyState:
    """Same rules as the v_journey_effective view. Keep the two in sync."""
    if journey.state == "booked" and journey.slot_start_at and now >= journey.slot_start_at:
        return "awaiting_result"
    is_waiting = journey.state in ("retake_later", "failed")
    if is_waiting and journey.next_bookable_at and now >= journey.next_bookable_at:
        return "eligible"
    return journey.state


async def transition(conn: Conn, before: JourneyRow, after: JourneyRow, audit: Audit) -> JourneyRow:
    """Persist a new journey row and its journey_events row. Caller holds the row lock."""
    if after.state not in TRANSITIONS[before.state]:
        raise app_error("invalid_transition")
    await journeys.save(conn, after)
    await journeys.insert_event(
        conn,
        EventIn(
            journey_id=after.id,
            from_state=before.state,
            to_state=after.state,
            actor_id=audit.actor.user_id if audit.actor else None,
            actor_role=audit.role,
            reason=audit.reason,
            meta=audit.meta,
        ),
    )
    return after


async def persist_derived(conn: Conn, journey: JourneyRow, now: datetime) -> JourneyRow:
    """Write a time-derived state (e.g. cooldown ended) before any other change."""
    derived = effective_state(journey, now)
    if derived == journey.state:
        return journey
    after = journey.model_copy(update={"state": derived})
    return await transition(conn, journey, after, Audit(actor=None, reason="derived_at_read"))
