"""Hourly job (PRD section 9): remind the interviewer at end + 2 h and + 20 h; at + 24 h tell
every admin the result is overdue. Idempotent: each reminder is sent once per booking."""

from datetime import datetime, timedelta

from app.core.clock import utc_now
from app.core.rules import IDEMPOTENCY_TTL, RESULT_OVERDUE_AFTER, RESULT_REMINDER_STAGES
from app.db.session import Conn
from app.repositories import admin_writes, idempotency, notifications, reminders
from app.repositories.reminders import MissingResult
from app.services import notify


def stage_label(delta: timedelta) -> str:
    return f"{int(delta.total_seconds() // 3600)}h"


def _values(item: MissingResult) -> dict[str, str]:
    return {
        "student": item.student_name,
        "interviewer": item.interviewer_name,
        "date": notify.ist_date(item.start_at),
        "start": notify.ist_time(item.start_at),
    }


async def _remind(conn: Conn, item: MissingResult, now: datetime) -> int:
    sent = 0
    for delta in RESULT_REMINDER_STAGES:
        extra = {"stage": stage_label(delta)}
        due = now >= item.end_at + delta
        if due and not await notifications.exists_for_booking(
            conn, "iv_result_reminder", item.booking_id, extra
        ):
            payload = {"booking_id": str(item.booking_id), **extra}
            await notify.send(
                conn, item.interviewer_id, "iv_result_reminder", _values(item), payload
            )
            sent += 1
    return sent


async def _escalate(conn: Conn, item: MissingResult, now: datetime) -> int:
    if now < item.end_at + RESULT_OVERDUE_AFTER:
        return 0
    sent = 0
    for admin_id in await admin_writes.admin_ids(conn):
        extra = {"admin_id": str(admin_id)}
        if not await notifications.exists_for_booking(
            conn, "admin_result_overdue", item.booking_id, extra
        ):
            payload = {"booking_id": str(item.booking_id), **extra}
            await notify.send(conn, admin_id, "admin_result_overdue", _values(item), payload)
            sent += 1
    return sent


async def run_result_reminders(conn: Conn) -> int:
    """Returns how many notifications were created."""
    now = utc_now()
    first_stage = min(RESULT_REMINDER_STAGES)
    sent = 0
    async with conn.transaction():
        if not await reminders.try_job_lock(conn):
            return 0
        for item in await reminders.missing_results(conn, now - first_stage):
            sent += await _remind(conn, item, now)
            sent += await _escalate(conn, item, now)
        await idempotency.purge_older_than(conn, now - IDEMPOTENCY_TTL)
    return sent
