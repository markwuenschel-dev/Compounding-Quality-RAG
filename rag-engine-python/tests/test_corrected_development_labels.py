from __future__ import annotations

import json
from pathlib import Path

from app.review_summary_evaluate import load_review_summary_extraction_cases


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT_PATH = (
    PROJECT_ROOT
    / "data"
    / "eval"
    / "review_summary_extraction_development.json"
)


def test_corrected_development_fixture_is_valid() -> None:
    cases = load_review_summary_extraction_cases(DEVELOPMENT_PATH)

    assert len(cases) == 20
    assert len({case["case_id"] for case in cases}) == 20


def test_completed_abstracted_reference_reviews_are_not_labeled_not_needed() -> None:
    cases = json.loads(DEVELOPMENT_PATH.read_text(encoding="utf-8"))

    for case in cases:
        note = case["reviewer_note"].lower()
        result = case["expected_review_summary"][
            "api_reference_review_result"
        ]

        if "the assessment incorporated" not in note:
            continue

        assert result != "not_needed"


def test_complaint_reported_hospitalization_is_proposed_for_confirmation() -> None:
    cases = {
        case["case_id"]: case
        for case in json.loads(DEVELOPMENT_PATH.read_text(encoding="utf-8"))
    }
    hospitalization_case = cases["DEV-EXT-007-PAIR-0036"]

    assert "hospitalized" in hospitalization_case["concern_text"].lower()
    assert "hospital" not in hospitalization_case["reviewer_note"].lower()
    assert hospitalization_case["expected_review_summary"][
        "severe_triggers_observed"
    ] == ["pet_hospitalization"]
