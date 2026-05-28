from __future__ import annotations

import json
from typing import Any

import pytest

from app.review_summary_extraction import (
    ReviewSummaryExtractionError,
    build_review_summary_prompt,
    extract_review_summary,
    parse_llm_json,
)
from app.schemas import (
    ApiReferenceReviewResult,
    EscalationTrigger,
    InventoryInspectionResult,
    LotBatchPatternSummary,
    RecordReviewResult,
)


class FakeLLMClient:
    def __init__(self, payload: dict[str, Any] | str) -> None:
        self.payload = payload
        self.prompts: list[str] = []

    def complete_json(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if isinstance(self.payload, str):
            return self.payload
        return json.dumps(self.payload)


def base_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "record_review_result": "no_discrepancy_found",
        "lot_batch_pattern_summary": "no_similar_batch_concerns_found",
        "inventory_inspection_result": "not_checked",
        "customer_context_summary": "Dog vomited once and recovered. No severe escalation trigger was observed.",
        "api_reference_review_result": "not_needed",
        "missing_information": [],
        "evidence_limitations": [],
        "severe_triggers_observed": [],
    }
    payload.update(overrides)
    return payload


def test_extract_review_summary_returns_validated_review_summary() -> None:
    note = (
        "I reviewed the record and found no discrepancy. No similar batch complaints were found. "
        "Inventory was not available. The dog vomited once about 10 minutes after dosing and recovered. "
        "No hospitalization, death, legal threat, contamination, wrong medication concern, or vet allegation was reported."
    )
    client = FakeLLMClient(
        base_payload(
            inventory_inspection_result="no_inventory_available",
            customer_context_summary="Dog vomited once about 10 minutes after dosing and recovered.",
            missing_information=["Exact dose administered by customer."],
            evidence_limitations=["Inventory was not available to inspect."],
        )
    )

    result = extract_review_summary(note, client)

    assert result.record_review_result == RecordReviewResult.NO_DISCREPANCY_FOUND
    assert result.lot_batch_pattern_summary == LotBatchPatternSummary.NO_SIMILAR_BATCH_CONCERNS_FOUND
    assert result.inventory_inspection_result == InventoryInspectionResult.NO_INVENTORY_AVAILABLE
    assert result.api_reference_review_result == ApiReferenceReviewResult.NOT_NEEDED
    assert result.missing_information == ["Exact dose administered by customer."]
    assert result.evidence_limitations == ["Inventory was not available to inspect."]
    assert result.severe_triggers_observed == []
    assert client.prompts
    assert "Return ONLY valid JSON" in client.prompts[0]


def test_prompt_lists_schema_fields_and_safety_rules() -> None:
    prompt = build_review_summary_prompt("Reviewer note")

    assert "record_review_result" in prompt
    assert "lot_batch_pattern_summary" in prompt
    assert "inventory_inspection_result" in prompt
    assert "api_reference_review_result" in prompt
    assert "severe_triggers_observed" in prompt
    assert "Only include a severe trigger when the reviewer affirmatively confirms it" in prompt
    assert "Reviewer note" in prompt


def test_parse_llm_json_accepts_fenced_json() -> None:
    payload = base_payload()
    raw_response = f"```json\n{json.dumps(payload)}\n```"

    assert parse_llm_json(raw_response) == payload


def test_parse_llm_json_accepts_surrounding_text_when_json_object_is_complete() -> None:
    payload = base_payload()
    raw_response = f"Here is the JSON:\n{json.dumps(payload)}\nDone."

    assert parse_llm_json(raw_response) == payload


def test_extract_review_summary_rejects_empty_note() -> None:
    with pytest.raises(ValueError, match="reviewer_note must not be empty"):
        extract_review_summary("   ", FakeLLMClient(base_payload()))


def test_extract_review_summary_rejects_empty_llm_response() -> None:
    with pytest.raises(ReviewSummaryExtractionError, match="empty"):
        extract_review_summary("Reviewer note", FakeLLMClient(""))


def test_extract_review_summary_rejects_invalid_json() -> None:
    with pytest.raises(ReviewSummaryExtractionError):
        extract_review_summary("Reviewer note", FakeLLMClient("not-json"))


def test_extract_review_summary_rejects_non_object_json() -> None:
    with pytest.raises(ReviewSummaryExtractionError, match="must be an object"):
        extract_review_summary("Reviewer note", FakeLLMClient("[]"))


def test_extract_review_summary_rejects_missing_required_field() -> None:
    payload = base_payload()
    del payload["record_review_result"]

    with pytest.raises(ReviewSummaryExtractionError, match="ReviewSummary"):
        extract_review_summary("Reviewer note", FakeLLMClient(payload))


def test_extract_review_summary_rejects_extra_fields_from_strict_model() -> None:
    payload = base_payload(unsupported_extra_field=True)

    with pytest.raises(ReviewSummaryExtractionError, match="ReviewSummary"):
        extract_review_summary("Reviewer note", FakeLLMClient(payload))


def test_extract_review_summary_normalizes_enum_names_and_case() -> None:
    payload = base_payload(
        record_review_result="NO_DISCREPANCY_FOUND",
        lot_batch_pattern_summary="No Similar Batch Concerns Found",
        inventory_inspection_result="Not Checked",
        api_reference_review_result="NOT_NEEDED",
    )

    result = extract_review_summary("Reviewer observed no severe trigger.", FakeLLMClient(payload))

    assert result.record_review_result == RecordReviewResult.NO_DISCREPANCY_FOUND
    assert result.lot_batch_pattern_summary == LotBatchPatternSummary.NO_SIMILAR_BATCH_CONCERNS_FOUND
    assert result.inventory_inspection_result == InventoryInspectionResult.NOT_CHECKED
    assert result.api_reference_review_result == ApiReferenceReviewResult.NOT_NEEDED


def test_extract_review_summary_normalizes_none_like_lists_and_empty_summary() -> None:
    payload = base_payload(
        customer_context_summary="",
        missing_information="None",
        evidence_limitations=["None", "", None],
        severe_triggers_observed=None,
    )

    result = extract_review_summary("Reviewer observed no severe trigger.", FakeLLMClient(payload))

    assert result.customer_context_summary is None
    assert result.missing_information == []
    assert result.evidence_limitations == []
    assert result.severe_triggers_observed == []


def test_negated_hospitalization_from_note_removes_erroneous_model_trigger() -> None:
    note = "Dog vomited once and recovered. No hospitalization was reported."
    payload = base_payload(
        severe_triggers_observed=["pet_hospitalization"],
        customer_context_summary="Dog vomited once and recovered. No hospitalization was reported.",
    )

    result = extract_review_summary(note, FakeLLMClient(payload))

    assert result.severe_triggers_observed == []


def test_negated_severe_terms_do_not_create_or_preserve_triggers() -> None:
    note = (
        "No hospitalization, no death, no legal threat, no contamination concern, "
        "no wrong medication concern, and no veterinarian allegation of harm were reported."
    )
    payload = base_payload(
        severe_triggers_observed=[
            "pet_hospitalization",
            "pet_death",
            "threatened_legal_action",
            "possible_contamination",
            "wrong_patient_or_wrong_medication",
            "veterinarian_alleges_harm_from_compound",
        ]
    )

    result = extract_review_summary(note, FakeLLMClient(payload))

    assert result.severe_triggers_observed == []


def test_confirmed_hospitalization_is_added_even_if_model_missed_it() -> None:
    note = "Reviewer confirmed the dog was hospitalized after administration."
    payload = base_payload(severe_triggers_observed=[])

    result = extract_review_summary(note, FakeLLMClient(payload))

    assert result.severe_triggers_observed == [EscalationTrigger.PET_HOSPITALIZATION]


def test_confirmed_wrong_medication_trigger_is_preserved() -> None:
    note = "Reviewer confirmed possible wrong patient or wrong medication issue. Severity is not yet known."
    payload = base_payload(
        record_review_result="documentation_discrepancy_found",
        lot_batch_pattern_summary="not_applicable",
        inventory_inspection_result="not_applicable",
        severe_triggers_observed=["wrong_patient_or_wrong_medication"],
    )

    result = extract_review_summary(note, FakeLLMClient(payload))

    assert result.record_review_result == RecordReviewResult.DOCUMENTATION_DISCREPANCY_FOUND
    assert result.severe_triggers_observed == [EscalationTrigger.WRONG_PATIENT_OR_WRONG_MEDICATION]


def test_severity_unknown_alone_does_not_create_severe_trigger() -> None:
    note = "Severity is not yet known. Reviewer has not confirmed hospitalization, death, legal threat, or wrong medication."
    payload = base_payload(severe_triggers_observed=[])

    result = extract_review_summary(note, FakeLLMClient(payload))

    assert result.severe_triggers_observed == []


def test_inventory_unavailable_note_overrides_not_checked_and_adds_limitation() -> None:
    note = "Inventory was not available to inspect during the review."
    payload = base_payload(
        inventory_inspection_result="not_checked",
        evidence_limitations=[],
    )

    result = extract_review_summary(note, FakeLLMClient(payload))

    assert result.inventory_inspection_result == InventoryInspectionResult.NO_INVENTORY_AVAILABLE
    assert result.evidence_limitations == ["Inventory was not available to inspect."]


def test_inventory_not_physically_inspected_adds_not_checked_limitation() -> None:
    note = "Device was not physically inspected by this tool."
    payload = base_payload(
        inventory_inspection_result="no_visual_concern_found",
        evidence_limitations=[],
    )

    result = extract_review_summary(note, FakeLLMClient(payload))

    assert result.inventory_inspection_result == InventoryInspectionResult.NOT_CHECKED
    assert result.evidence_limitations == ["Inventory was not inspected."]


def test_external_reference_unsupported_note_sets_public_corpus_limitation() -> None:
    note = "Plumb's external reference was requested but is not supported by the public synthetic corpus."
    payload = base_payload(
        api_reference_review_result="external_reference_needed",
        evidence_limitations=[],
    )

    result = extract_review_summary(note, FakeLLMClient(payload))

    assert result.api_reference_review_result == ApiReferenceReviewResult.NOT_SUPPORTED_BY_PUBLIC_CORPUS
    assert result.evidence_limitations == [
        "External drug-reference information was not supported by the public synthetic corpus."
    ]


def test_external_reference_needed_is_preserved_when_not_unsupported() -> None:
    note = "External drug reference needed for pharmacist review."
    payload = base_payload(api_reference_review_result="not_needed")

    result = extract_review_summary(note, FakeLLMClient(payload))

    assert result.api_reference_review_result == ApiReferenceReviewResult.EXTERNAL_REFERENCE_NEEDED


def test_synthetic_reference_consulted_is_detected() -> None:
    note = "Synthetic reference consulted during the demo review."
    payload = base_payload(api_reference_review_result="not_needed")

    result = extract_review_summary(note, FakeLLMClient(payload))

    assert result.api_reference_review_result == ApiReferenceReviewResult.SYNTHETIC_REFERENCE_CONSULTED


def test_duplicate_missing_information_and_limitations_are_deduplicated_in_order() -> None:
    payload = base_payload(
        missing_information=["Dose administered.", "Dose administered.", "Vet contacted?"],
        evidence_limitations=["Inventory unavailable.", "Inventory unavailable."],
    )

    result = extract_review_summary("Reviewer observed no severe trigger.", FakeLLMClient(payload))

    assert result.missing_information == ["Dose administered.", "Vet contacted?"]
    assert result.evidence_limitations == ["Inventory unavailable."]


def test_bud_question_style_payload_validates_not_applicable_inventory() -> None:
    note = "Frontline pharmacist requested BUD clarification. Reviewer observed no severe escalation trigger."
    payload = base_payload(
        inventory_inspection_result="not_applicable",
        customer_context_summary="Frontline pharmacist requested BUD clarification.",
        missing_information=[
            "Preparation date.",
            "Assigned beyond-use date.",
            "Dispense or review date.",
        ],
    )

    result = extract_review_summary(note, FakeLLMClient(payload))

    assert result.inventory_inspection_result == InventoryInspectionResult.NOT_APPLICABLE
    assert result.missing_information == [
        "Preparation date.",
        "Assigned beyond-use date.",
        "Dispense or review date.",
    ]
    assert result.severe_triggers_observed == []

def test_confirmed_wrong_medication_after_negated_other_triggers_is_preserved() -> None:
    note = (
        "No hospitalization, death, or legal threat was reported. "
        "Reviewer confirmed possible wrong medication."
    )
    payload = base_payload(severe_triggers_observed=[])

    result = extract_review_summary(note, FakeLLMClient(payload))

    assert result.severe_triggers_observed == [
        EscalationTrigger.WRONG_PATIENT_OR_WRONG_MEDICATION
    ]