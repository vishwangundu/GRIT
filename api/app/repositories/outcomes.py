"""SQL for interview_outcomes."""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.core.rules import OutcomeResult
from app.db.session import Conn
from app.repositories.rows import OutcomeRow

_SELECT = """
select id, booking_id, journey_id, interviewer_id, result, feedback_to_student,
       attempt_counted, prev_snapshot, recorded_at, locked_at
from interview_outcomes
"""


@dataclass(frozen=True)
class OutcomeFields:
    result: OutcomeResult
    rubric: dict[str, int] | None
    feedback_to_student: str
    internal_notes: str
    retake_after: datetime | None
    attempt_counted: bool


@dataclass(frozen=True)
class OutcomeIn:
    booking_id: UUID
    journey_id: UUID
    interviewer_id: UUID
    recorded_by: UUID
    fields: OutcomeFields
    prev_snapshot: dict[str, Any]
    recorded_at: datetime
    locked_at: datetime


def _rubric_json(rubric: dict[str, int] | None) -> str | None:
    return json.dumps(rubric) if rubric is not None else None


def _to_row(raw: dict[str, Any]) -> OutcomeRow:
    snapshot = raw["prev_snapshot"]
    raw["prev_snapshot"] = json.loads(snapshot) if isinstance(snapshot, str) else snapshot
    return OutcomeRow.model_validate(raw)


async def insert(conn: Conn, outcome: OutcomeIn) -> OutcomeRow:
    f = outcome.fields
    row = await conn.fetchrow(
        """
        insert into interview_outcomes
          (booking_id, journey_id, interviewer_id, result, rubric, feedback_to_student,
           internal_notes, retake_after, attempt_counted, prev_snapshot, recorded_by,
           recorded_at, locked_at)
        values ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10::jsonb, $11, $12, $13)
        returning id, booking_id, journey_id, interviewer_id, result, feedback_to_student,
                  attempt_counted, prev_snapshot, recorded_at, locked_at
        """,
        outcome.booking_id,
        outcome.journey_id,
        outcome.interviewer_id,
        f.result,
        _rubric_json(f.rubric),
        f.feedback_to_student,
        f.internal_notes,
        f.retake_after,
        f.attempt_counted,
        json.dumps(outcome.prev_snapshot, default=str),
        outcome.recorded_by,
        outcome.recorded_at,
        outcome.locked_at,
    )
    if row is None:
        raise RuntimeError("insert into interview_outcomes returned no row")
    return _to_row(dict(row))


async def get_by_booking(conn: Conn, booking_id: UUID) -> OutcomeRow | None:
    row = await conn.fetchrow(_SELECT + " where booking_id = $1", booking_id)
    return _to_row(dict(row)) if row else None


async def update(
    conn: Conn, outcome_id: UUID, fields: OutcomeFields, edit: tuple[datetime, str | None]
) -> None:
    edited_at, edit_note = edit
    await conn.execute(
        """
        update interview_outcomes
        set result = $2, rubric = $3::jsonb, feedback_to_student = $4, internal_notes = $5,
            retake_after = $6, attempt_counted = $7, edited_at = $8, edit_note = $9
        where id = $1
        """,
        outcome_id,
        fields.result,
        _rubric_json(fields.rubric),
        fields.feedback_to_student,
        fields.internal_notes,
        fields.retake_after,
        fields.attempt_counted,
        edited_at,
        edit_note,
    )
