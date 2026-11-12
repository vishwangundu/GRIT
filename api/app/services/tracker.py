"""Admin tracker (FR-A1 to FR-A5): tiles plus the rows of one tab."""

from datetime import datetime

from app.core.clock import utc_now
from app.core.rules import NUDGE_COOLDOWN, RESULT_OVERDUE_AFTER, SLOW_AFTER_DAYS
from app.db.session import Conn
from app.repositories import tracker
from app.repositories.tracker import AwaitingRaw, NotBookedRaw
from app.schemas.admin import (
    AwaitingRow,
    BadgeOptionOut,
    BookedRow,
    NotBookedRow,
    ResultRow,
    TilesOut,
    TrackerResponse,
    TrackerTab,
    WaitStatus,
)
from app.services.notify import badge_label


def wait_status(row: NotBookedRaw) -> WaitStatus:
    if row.effective_state == "retake_later":
        return "retake_until"
    if row.effective_state == "failed":
        return "cooldown_until"
    if row.priority:
        return "needs_rebooking"
    return "can_rebook" if row.has_outcome else "not_booked"


def not_booked_row(row: NotBookedRaw, now: datetime) -> NotBookedRow:
    days = (now - row.eligible_at).days if row.eligible_at else None
    status = wait_status(row)
    recently = row.last_nudged_at is not None and now - row.last_nudged_at < NUDGE_COOLDOWN
    return NotBookedRow(
        student_id=row.student_id,
        name=row.name,
        campus=row.campus,
        effective_state=row.effective_state,
        status=status,
        until=row.next_bookable_at if status in ("retake_until", "cooldown_until") else None,
        days_since_eligible=days,
        is_slow=days is not None and days >= SLOW_AFTER_DAYS,
        priority=row.priority,
        last_nudged_at=row.last_nudged_at,
        can_nudge=row.effective_state == "eligible" and not recently,
    )


def awaiting_row(row: AwaitingRaw, now: datetime) -> AwaitingRow:
    due_at = row.end_at + RESULT_OVERDUE_AFTER
    status = "in_progress" if now < row.end_at else ("overdue" if now >= due_at else "due")
    return AwaitingRow(**row.model_dump(), status=status, due_at=due_at)


async def get_tracker(conn: Conn, badge_id: int | None, tab: TrackerTab) -> TrackerResponse:
    now = utc_now()
    tiles = await tracker.tiles(conn, badge_id, now, RESULT_OVERDUE_AFTER)
    badges = [
        BadgeOptionOut(id=b.id, name=badge_label(b.level), track=b.track_name)
        for b in await tracker.badge_options(conn)
    ]
    response = TrackerResponse(
        tab=tab, badges=badges, tiles=TilesOut.model_validate(tiles.model_dump())
    )
    match tab:
        case "notbooked":
            rows = await tracker.not_booked(conn, badge_id)
            response.not_booked_rows = [not_booked_row(r, now) for r in rows]
        case "booked":
            booked = await tracker.booked(conn, badge_id, "booked")
            response.booked_rows = [
                BookedRow(
                    **r.model_dump(exclude={"reschedule_count"}),
                    reschedules_used=r.reschedule_count,
                )
                for r in booked
            ]
        case "awaiting":
            waiting = await tracker.awaiting(conn, badge_id)
            response.awaiting_rows = [awaiting_row(r, now) for r in waiting]
        case "results":
            results = await tracker.results(conn, badge_id)
            response.result_rows = [ResultRow.model_validate(r.model_dump()) for r in results]
    return response
