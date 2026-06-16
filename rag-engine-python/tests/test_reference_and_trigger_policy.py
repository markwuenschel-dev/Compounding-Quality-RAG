from __future__ import annotations

import json

from app.review_summary_extraction import (
    extract_review_summary,
    extract_review_summary_result,
    infer_grounded_missing_information,
)
from app.schemas import (
    ApiReferenceReviewResult,
    EscalationTrigger,
)


class StubClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def complete_json(self, prompt: str) -> str:
        return json.dumps(self.payload)


def base_payload() -> dict[str, object]:
    return {
        "record_review_result": "not_applicable",
        "lot_batch_pattern_summary": "not_applicable",
        "inventory_inspection_result": "not_applicable",
        "customer_context_summary": None,
        "api_reference_review_result": "not_needed",
        "missing_information": [],
        "evidence_limitations": [],
        "severe_triggers_observed": [],
    }


def test_external_reference_consulted_is_a_schema_value() -> None:
    assert (
        ApiReferenceReviewResult.EXTERNAL_REFERENCE_CONSULTED.value
        == "external_reference_consulted"
    )


def test_completed_external_review_is_grounded() -> None:
    summary = extract_review_summary(
        "The assessment incorporated USP guidance.",
        StubClient(base_payload()),
    )

    assert (
        summary.api_reference_review_result
        == ApiReferenceReviewResult.EXTERNAL_REFERENCE_CONSULTED
    )


def test_non_disclosure_overrides_completed_external_review() -> None:
    summary = extract_review_summary(
        (
            "The assessment incorporated manufacturer information. "
            "Specific supplier or manufacturer details were not disclosed."
        ),
        StubClient(base_payload()),
    )

    assert (
        summary.api_reference_review_result
        == ApiReferenceReviewResult.NOT_SUPPORTED_BY_PUBLIC_CORPUS
    )


def test_complaint_reported_hospitalization_is_proposed_for_confirmation() -> None:
    result = extract_review_summary_result(
        reviewer_note=(
            "Compounding-record review found no documented discrepancy. "
            "No additional quality complaints were identified for the lot."
        ),
        concern_text="The pet was hospitalized after the first dose.",
        llm_client=StubClient(base_payload()),
    )

    assert result.review_summary.severe_triggers_observed == [
        EscalationTrigger.PET_HOSPITALIZATION
    ]


def test_context_only_symptoms_do_not_create_new_severe_trigger() -> None:
    result = extract_review_summary_result(
        reviewer_note="Serious clinical context included respiratory distress.",
        concern_text=(
            "The pet looked short of breath and later fell over, "
            "but was not hospitalized."
        ),
        llm_client=StubClient(base_payload()),
    )

    assert result.review_summary.severe_triggers_observed == []


def test_canonical_unresolved_commands_become_missing_information() -> None:
    note = (
        "Unresolved investigation items: Confirm storage and temperature "
        "conditions. Confirm shaking and resuspension technique. "
        "Clarify the event timeline. Determine whether there was a confirmed "
        "shortage."
    )

    assert infer_grounded_missing_information(note, []) == [
        "Storage and temperature conditions",
        "Shaking and resuspension technique",
        "Event timeline",
        "Whether there was a confirmed shortage",
    ]
