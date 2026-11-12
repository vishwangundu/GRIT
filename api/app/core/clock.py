"""Single source of the current time, always timezone-aware UTC."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)
