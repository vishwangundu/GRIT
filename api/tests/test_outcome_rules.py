"""Pure validation rules for results (FR-I3). No database needed."""

from datetime import timedelta

import pytest

from app.core.clock import utc_now
from app.core.errors import AppError
from app.core.rules import IST
from app.schemas.outcome import OutcomeCreate
from app.services.outcome_rules import validate

RUBRIC = {"problem_solving": 3, "product_thinking": 2, "code_walkthrough": 2, "communication": 3}
FEEDBACK = "Explain how you tested the project."


@pytest.mark.parametrize(
    "rubric",
    [
        None,
        {"problem_solving": 3, "product_thinking": 2, "code_walkthrough": 2},
        {**RUBRIC, "communication": 5},
        {**RUBRIC, "communication": 0},
        {**RUBRIC, "extra": 2},
    ],
)
def test_incomplete_or_out_of_range_rubric_is_rejected(rubric: dict[str, int] | None) -> None:
    with pytest.raises(AppError) as err:
        validate(OutcomeCreate(result="pass", rubric=rubric), utc_now())
    assert err.value.code == "rubric_incomplete"


def test_no_show_needs_no_rubric_or_feedback() -> None:
    fields = validate(OutcomeCreate(result="no_show"), utc_now())
    assert fields.rubric is None
    assert fields.attempt_counted is True


@pytest.mark.parametrize("result", ["fail", "retake_later"])
def test_short_feedback_is_rejected_for_fail_and_retake(result: str) -> None:
    data = OutcomeCreate.model_validate(
        {"result": result, "rubric": RUBRIC, "feedback_to_student": "  too short     "}
    )
    with pytest.raises(AppError) as err:
        validate(data, utc_now())
    assert err.value.code == "feedback_required"


def test_pass_feedback_is_optional() -> None:
    fields = validate(OutcomeCreate(result="pass", rubric=RUBRIC), utc_now())
    assert fields.feedback_to_student == ""
    assert fields.attempt_counted is False


@pytest.mark.parametrize("days", [None, 0, -1])
def test_retake_date_must_be_in_the_future(days: int | None) -> None:
    today = utc_now().astimezone(IST).date()
    retake = None if days is None else today + timedelta(days=days)
    data = OutcomeCreate(
        result="retake_later", rubric=RUBRIC, feedback_to_student=FEEDBACK, retake_after=retake
    )
    with pytest.raises(AppError) as err:
        validate(data, utc_now())
    assert err.value.code == "retake_date_invalid"
