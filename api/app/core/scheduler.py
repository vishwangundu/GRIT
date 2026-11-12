"""In-process scheduler: runs the result-reminder job every SCHEDULER_INTERVAL."""

import asyncio
import contextlib
import logging

from app.core.rules import SCHEDULER_INTERVAL
from app.db.session import Pool
from app.services.reminders import run_result_reminders

logger = logging.getLogger(__name__)


async def _loop(pool: Pool) -> None:
    while True:
        try:
            async with pool.acquire() as conn:
                sent = await run_result_reminders(conn)
            logger.info("result_reminders_ran", extra={"sent": sent})
        except Exception:
            logger.exception("result_reminders_failed")
        await asyncio.sleep(SCHEDULER_INTERVAL.total_seconds())


def start(pool: Pool) -> "asyncio.Task[None]":
    return asyncio.create_task(_loop(pool), name="result-reminders")


async def stop(task: "asyncio.Task[None]") -> None:
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
