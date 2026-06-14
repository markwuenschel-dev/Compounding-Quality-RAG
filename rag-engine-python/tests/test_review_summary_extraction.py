import json

from app.review_summary_extraction import extract_review_summary_result


class FakeClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def complete_json(self, prompt: str) -> str:
        return json.dumps(self.payload)


def test_extract_review_summary_result_preserves_negated_severe_triggers() -> None:
    client = FakeClient(
        {
            "record_review_result": "No discrepancy found",
            "lot_batch_pattern_summary": "No similar batch concerns found",
            "inventory_inspection_result": "No inventory available",
            "customer_context_summary": "Dog vomited once and recovered.",
            "api_reference_review_result": "Not needed",
            "missing_information": ["Exact dose administered"],
            "evidence_limitations": [],
            "severe_triggers_observed": [
                "pet_hospitalization",
                "possible_contamination",
            ],
        }
    )

    result = extract_review_summary_result(
        reviewer_note=(
            "Checked formula and worksheet, nothing off. "
            "No inventory available to inspect. "
            "Dog vomited once and recovered. "
            "No hospitalization and no contamination."
        ),
        llm_client=client,
        concern_text="Dog vomited after the dose.",
    )

    assert result.review_summary.severe_triggers_observed == []
    assert (
        result.review_summary.inventory_inspection_result.value
        == "no_inventory_available"
    )
    assert "Inventory was not available to inspect." in (
        result.review_summary.evidence_limitations
    )


def test_field_evidence_quotes_are_taken_from_reviewer_note() -> None:
    note = (
        "Worksheet review found no discrepancy. "
        "Same lot had no similar concerns. "
        "Inventory was not available to inspect."
    )
    client = FakeClient(
        {
            "record_review_result": "no_discrepancy_found",
            "lot_batch_pattern_summary": "no_similar_batch_concerns_found",
            "inventory_inspection_result": "no_inventory_available",
            "customer_context_summary": None,
            "api_reference_review_result": "not_needed",
            "missing_information": [],
            "evidence_limitations": [],
            "severe_triggers_observed": [],
        }
    )

    result = extract_review_summary_result(
        reviewer_note=note,
        llm_client=client,
    )

    quotes = [
        item.supporting_quote
        for item in result.field_evidence
        if item.supporting_quote is not None
    ]

    assert quotes
    assert all(quote in note for quote in quotes)


def test_grounding_corrects_scalar_fields_and_filters_unstated_missing_items() -> None:
    client = FakeClient(
        {
            "record_review_result": "documentation_incomplete",
            "lot_batch_pattern_summary": "trend_threshold_met",
            "inventory_inspection_result": "visual_concern_found",
            "customer_context_summary": "Customer could not confirm dispensing.",
            "api_reference_review_result": "external_reference_needed",
            "missing_information": [
                "Medication name",
                "Customer phone number",
                "Whether medication dispensed from the device",
            ],
            "evidence_limitations": [],
            "severe_triggers_observed": [],
        }
    )

    result = extract_review_summary_result(
        reviewer_note=(
            "Record review found no discrepancy. "
            "Lot trend unavailable. "
            "Inventory was not inspected. "
            "Customer could not confirm whether anything dispensed. "
            "External reference not needed."
        ),
        llm_client=client,
        concern_text="The transdermal pen clicked but dispensing is uncertain.",
    )

    summary = result.review_summary

    assert summary.record_review_result.value == "no_discrepancy_found"
    assert summary.lot_batch_pattern_summary.value == "unavailable"
    assert summary.inventory_inspection_result.value == "not_checked"
    assert summary.api_reference_review_result.value == "not_needed"
    assert summary.missing_information == [
        "Whether medication dispensed from the device"
    ]


def test_same_batch_with_no_similar_concerns_is_not_a_repeat_issue_trigger() -> None:
    client = FakeClient(
        {
            "record_review_result": "no_discrepancy_found",
            "lot_batch_pattern_summary": "no_similar_batch_concerns_found",
            "inventory_inspection_result": "no_inventory_available",
            "customer_context_summary": "Dog was hospitalized.",
            "api_reference_review_result": "external_reference_needed",
            "missing_information": [],
            "evidence_limitations": [],
            "severe_triggers_observed": [
                "pet_hospitalization",
                "repeat_issue_same_lot_or_batch_with_conditions",
            ],
        }
    )

    result = extract_review_summary_result(
        reviewer_note=(
            "Worksheet review found no discrepancy. "
            "Same batch had no similar concerns. "
            "Inventory unavailable. "
            "Owner reported the dog was admitted to an emergency hospital. "
            "External reference needed."
        ),
        llm_client=client,
    )

    assert [
        trigger.value
        for trigger in result.review_summary.severe_triggers_observed
    ] == ["pet_hospitalization"]


def test_grounding_recognizes_ruled_out_and_confirmed_quality_findings() -> None:
    client = FakeClient(
        {
            "record_review_result": "documentation_incomplete",
            "lot_batch_pattern_summary": "unavailable",
            "inventory_inspection_result": "not_checked",
            "customer_context_summary": None,
            "api_reference_review_result": "external_reference_needed",
            "missing_information": ["Medication name"],
            "evidence_limitations": [],
            "severe_triggers_observed": [
                "possible_contamination",
                "wrong_patient_or_wrong_medication",
            ],
        }
    )

    result = extract_review_summary_result(
        reviewer_note=(
            "Record and label review confirmed the correct medication and patient. "
            "No similar batch complaints. "
            "Inventory inspection found no visual concern. "
            "Contamination was ruled out. "
            "No external reference was needed."
        ),
        llm_client=client,
    )

    summary = result.review_summary

    assert summary.record_review_result.value == "no_discrepancy_found"
    assert (
        summary.lot_batch_pattern_summary.value
        == "no_similar_batch_concerns_found"
    )
    assert summary.inventory_inspection_result.value == "no_visual_concern_found"
    assert summary.api_reference_review_result.value == "not_needed"
    assert summary.missing_information == []
    assert summary.severe_triggers_observed == []


def test_grounding_recognizes_confirmed_wrong_patient_case() -> None:
    client = FakeClient(
        {
            "record_review_result": "no_discrepancy_found",
            "lot_batch_pattern_summary": "unavailable",
            "inventory_inspection_result": "not_checked",
            "customer_context_summary": None,
            "api_reference_review_result": "external_reference_needed",
            "missing_information": [],
            "evidence_limitations": [],
            "severe_triggers_observed": [],
        }
    )

    result = extract_review_summary_result(
        reviewer_note=(
            "Record review confirmed the label was for a different patient. "
            "Lot review not applicable. "
            "Inventory inspection not applicable. "
            "No external reference needed."
        ),
        llm_client=client,
    )

    summary = result.review_summary

    assert summary.record_review_result.value == "documentation_discrepancy_found"
    assert summary.lot_batch_pattern_summary.value == "not_applicable"
    assert summary.inventory_inspection_result.value == "not_applicable"
    assert summary.api_reference_review_result.value == "not_needed"
    assert [
        trigger.value
        for trigger in summary.severe_triggers_observed
    ] == ["wrong_patient_or_wrong_medication"]


def test_no_inventory_left_is_grounded_as_unavailable() -> None:
    client = FakeClient(
        {
            "record_review_result": "no_discrepancy_found",
            "lot_batch_pattern_summary": "no_similar_batch_concerns_found",
            "inventory_inspection_result": "visual_concern_found",
            "customer_context_summary": None,
            "api_reference_review_result": "not_needed",
            "missing_information": [],
            "evidence_limitations": [],
            "severe_triggers_observed": [],
        }
    )

    result = extract_review_summary_result(
        reviewer_note="No inventory left to inspect.",
        llm_client=client,
    )

    assert (
        result.review_summary.inventory_inspection_result.value
        == "no_inventory_available"
    )
    assert "Inventory was not available to inspect." in (
        result.review_summary.evidence_limitations
    )
