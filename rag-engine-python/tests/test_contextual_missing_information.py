from app.contextual_missing_information import (
    build_decision_relevant_questions,
)
from app.schemas import ReviewSummary


def test_vomiting_questions_exclude_facts_already_documented() -> None:
    summary = ReviewSummary.model_validate(
        {
            "record_review_result": "no_discrepancy_found",
            "lot_batch_pattern_summary": "no_similar_batch_concerns_found",
            "inventory_inspection_result": "no_inventory_available",
            "customer_context_summary": "Dog vomited and recovered.",
            "api_reference_review_result": "not_needed",
            "missing_information": [],
            "evidence_limitations": [],
            "severe_triggers_observed": [],
        }
    )

    questions = build_decision_relevant_questions(
        concern_text="Dog vomited after an oral liquid.",
        reviewer_note=(
            "Owner reported vomiting 10 minutes after 2 mL. "
            "Dog is fine now. No ER visit. Veterinarian was not contacted."
        ),
        review_summary=summary,
    )

    assert [question.field_name for question in questions] == []


def test_vomiting_questions_include_only_unresolved_decision_fields() -> None:
    summary = ReviewSummary.model_validate(
        {
            "record_review_result": "no_discrepancy_found",
            "lot_batch_pattern_summary": "unavailable",
            "inventory_inspection_result": "not_checked",
            "customer_context_summary": None,
            "api_reference_review_result": "not_needed",
            "missing_information": [],
            "evidence_limitations": [],
            "severe_triggers_observed": [],
        }
    )

    questions = build_decision_relevant_questions(
        concern_text="Dog vomited after medication.",
        reviewer_note="Record review was normal.",
        review_summary=summary,
    )

    assert {
        question.field_name
        for question in questions
    } == {
        "hospitalization_status",
        "symptom_resolution",
        "veterinarian_contact",
        "dose_administered",
        "event_timing",
    }


def test_uncertain_device_dispensing_remains_an_unresolved_question() -> None:
    summary = ReviewSummary.model_validate(
        {
            "record_review_result": "no_discrepancy_found",
            "lot_batch_pattern_summary": "unavailable",
            "inventory_inspection_result": "not_checked",
            "customer_context_summary": None,
            "api_reference_review_result": "not_needed",
            "missing_information": [
                "Whether medication dispensed from the device"
            ],
            "evidence_limitations": [],
            "severe_triggers_observed": [],
        }
    )

    questions = build_decision_relevant_questions(
        concern_text="The transdermal pen clicked but dispensing is uncertain.",
        reviewer_note="Customer could not confirm whether anything dispensed.",
        review_summary=summary,
    )

    assert [question.field_name for question in questions] == [
        "device_dispense_status"
    ]


def test_confirmed_correct_medication_and_patient_does_not_create_question() -> None:
    summary = ReviewSummary.model_validate(
        {
            "record_review_result": "no_discrepancy_found",
            "lot_batch_pattern_summary": "no_similar_batch_concerns_found",
            "inventory_inspection_result": "no_visual_concern_found",
            "customer_context_summary": None,
            "api_reference_review_result": "not_needed",
            "missing_information": [],
            "evidence_limitations": [],
            "severe_triggers_observed": [],
        }
    )

    questions = build_decision_relevant_questions(
        concern_text="Customer worried this might be the wrong medication.",
        reviewer_note=(
            "Record review confirmed the correct medication and patient."
        ),
        review_summary=summary,
    )

    assert questions == []
