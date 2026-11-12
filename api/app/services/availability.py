"""Interviewer availability (I1, FR-I5): add windows, list them, block slots, remove windows."""

from datetime import date, datetime, time, timedelta
from uuid import UUID

from app.core.clock import utc_now
from app.core.errors import app_error
from app.core.rules import AVAILABILITY_HORIZON, IST, SLOT_MINUTES
from app.db.session import Conn
from app.deps.auth import Actor
from app.repositories import availability
from app.repositories.availability import WindowSlot
from app.schemas.interviewer import (
    AvailabilityResponse,
    AvailabilitySlot,
    AvailabilityWindow,
    WindowCreate,
    WindowCreated,
)

_SLOT_STEP = timedelta(minutes=SLOT_MINUTES)


def _parse_ist(day: date, hhmm: str) -> datetime:
    hours, minutes = (int(part) for part in hhmm.split(":"))
    if minutes % SLOT_MINUTES:
        raise app_error("not_half_hour")
    return datetime.combine(day, time(hours, minutes), tzinfo=IST)


def window_span(body: WindowCreate, now: datetime) -> tuple[datetime, datetime]:
    """Validate an IST window from the form and return it in UTC."""
    start = _parse_ist(body.date, body.start)
    end = _parse_ist(body.date, body.end)
    if end <= start:
        raise app_error("invalid_window")
    if start <= now:
        raise app_error("in_past")
    if start > now + AVAILABILITY_HORIZON:
        raise app_error("beyond_horizon")
    return start, end


def slot_starts(span: tuple[datetime, datetime]) -> list[datetime]:
    starts: list[datetime] = []
    current = span[0]
    while current + _SLOT_STEP <= span[1]:
        starts.append(current)
        current += _SLOT_STEP
    return starts


async def add_window(conn: Conn, actor: Actor, body: WindowCreate) -> WindowCreated:
    span = window_span(body, utc_now())
    async with conn.transaction():
        window_id = await availability.insert_window(conn, actor.user_id, span)
        created = 0
        for start in slot_starts(span):
            slot_span = (start, start + _SLOT_STEP)
            created += int(
                await availability.insert_slot(conn, window_id, actor.user_id, slot_span)
            )
    return WindowCreated(window_id=window_id, slots_created=created)


def _first_name(full_name: str | None) -> str | None:
    return full_name.split()[0] if full_name else None


def group_windows(rows: list[WindowSlot]) -> list[AvailabilityWindow]:
    windows: dict[UUID, AvailabilityWindow] = {}
    for row in rows:
        window = windows.setdefault(
            row.window_id,
            AvailabilityWindow(
                window_id=row.window_id,
                starts_at=row.window_starts_at,
                ends_at=row.window_ends_at,
                can_remove=True,
                slots=[],
            ),
        )
        if row.slot_id is None or row.start_at is None or row.end_at is None:
            continue
        status = row.status if row.status in ("open", "booked", "blocked") else "cancelled"
        window.slots.append(
            AvailabilitySlot(
                slot_id=row.slot_id,
                start_at=row.start_at,
                end_at=row.end_at,
                status=status,
                student_first_name=_first_name(row.student_name),
                booking_id=row.booking_id,
            )
        )
        if row.booking_id is not None:
            window.can_remove = False
    return list(windows.values())


async def list_windows(
    conn: Conn, actor: Actor, first: date | None, last: date | None
) -> AvailabilityResponse:
    today = utc_now().astimezone(IST).date()
    start = datetime.combine(first or today, time.min, tzinfo=IST)
    end_day = last or (today + AVAILABILITY_HORIZON)
    end = datetime.combine(end_day + timedelta(days=1), time.min, tzinfo=IST)
    rows = await availability.windows_with_slots(conn, actor.user_id, (start, end))
    return AvailabilityResponse(windows=group_windows(rows))


async def remove_window(conn: Conn, actor: Actor, window_id: UUID) -> bool:
    async with conn.transaction():
        window = await availability.get_window(conn, window_id)
        if window is None or window.deleted_at is not None:
            raise app_error("window_not_found")
        if window.interviewer_id != actor.user_id:
            raise app_error("forbidden")
        if await availability.confirmed_bookings_in_window(conn, window_id):
            raise app_error("window_has_bookings")
        await availability.soft_delete_window(conn, window_id, utc_now())
    return True


async def set_blocked(conn: Conn, actor: Actor, slot_id: UUID, blocked: bool) -> str:
    change = ("open", "blocked") if blocked else ("blocked", "open")
    if not await availability.toggle_block(conn, slot_id, actor.user_id, change):
        raise app_error("slot_not_changeable")
    return change[1]
