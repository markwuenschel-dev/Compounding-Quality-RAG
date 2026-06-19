from app.contextual_missing_information import (
    build_decision_relevant_questions,
)
from app.schemas import ReviewSummary


def summary() -> ReviewSummary:
    return ReviewSummary.model_validate(
        {
            "record_review_result": "no_discrepancy_found",
            "lot_batch_pattern_summary": "no_similar_batch_concerns_found",
            "inventory_inspection_result": "not_checked",
            "api_reference_review_result": "not_needed",
            "missing_information": [],
            "evidence_limitations": [],
            "severe_triggers_observed": [],
        }
    )


def field_names(concern_text: str, reviewer_note: str = "") -> list[str]:
    return [
        question.field_name
        for question in build_decision_relevant_questions(
            concern_text=concern_text,
            reviewer_note=reviewer_note,
            review_summary=summary(),
        )
    ]


def test_product_strength_and_package_quantity_are_not_administered_dose() -> None:
    fields = field_names(
        "The dog vomited and was hospitalized after the first dose of a "
        "15 mg/mL, 30 mL oral liquid."
    )

    assert "dose_administered" in fields


def test_actual_administered_dose_resolves_dose_question() -> None:
    fields = field_names(
        "The dog vomited after the owner gave 0.1 mL of the medication."
    )

    assert "dose_administered" not in fields


def test_clicks_used_as_directions_do_not_create_device_question() -> None:
    fields = field_names(
        "The pet developed sores after transdermal use. "
        "The directions say 2 clicks equals 0.1 mL."
    )

    assert "device_dispense_status" not in fields


def test_click_output_failure_creates_device_question() -> None:
    fields = field_names(
        "The pen clicks, but no medication comes out."
    )

    assert "device_dispense_status" in fields
