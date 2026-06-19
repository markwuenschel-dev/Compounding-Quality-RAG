from app.contextual_missing_information import (
    build_decision_relevant_questions,
)
from app.schemas import ReviewSummary


def summary() -> ReviewSummary:
    return ReviewSummary.model_validate(
        {
            "record_review_result": "not_applicable",
            "lot_batch_pattern_summary": "not_applicable",
            "inventory_inspection_result": "not_applicable",
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


def test_oral_suspension_does_not_trigger_device_question_from_pen_substring() -> None:
    assert "device_dispense_status" not in field_names(
        "What inactive ingredients are in the oral suspension?"
    )


def test_transdermal_skin_reaction_without_device_failure_does_not_trigger_device_question() -> None:
    assert "device_dispense_status" not in field_names(
        "The pet developed sores after transdermal application."
    )


def test_actual_pen_dispensing_problem_triggers_device_question() -> None:
    assert "device_dispense_status" in field_names(
        "The transdermal pen clicks but no medication comes out."
    )


def test_bud_word_without_actual_dates_still_requires_date_context() -> None:
    assert "bud_date_context" in field_names(
        "What is the degradation rate 20 days after the BUD?"
    )
