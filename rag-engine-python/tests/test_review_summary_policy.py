from app.review_summary_policy import (
    ReviewSummaryScope,
    apply_review_summary_defaults,
    infer_review_summary_scope,
)
from app.schemas import ReviewSummary


def model_summary() -> ReviewSummary:
    return ReviewSummary(
        record_review_result="no_discrepancy_found",
        lot_batch_pattern_summary="no_similar_batch_concerns_found",
        inventory_inspection_result="no_visual_concern_found",
        api_reference_review_result="external_reference_consulted",
        missing_information=[],
        evidence_limitations=[],
        severe_triggers_observed=[],
    )


def test_guidance_only_defaults_ignore_unsupported_model_claims() -> None:
    result = apply_review_summary_defaults(
        model_summary(),
        concern_text=(
            "Can you tell me whether storing this medication in the refrigerator "
            "is acceptable?"
        ),
        reviewer_note="Storage and temperature conditions still need confirmation.",
    )

    assert result.record_review_result.value == "not_applicable"
    assert result.lot_batch_pattern_summary.value == "not_applicable"
    assert result.inventory_inspection_result.value == "not_applicable"
    assert result.api_reference_review_result.value == "not_needed"


def test_full_investigation_defaults_undocumented_reviews() -> None:
    result = apply_review_summary_defaults(
        model_summary(),
        concern_text=(
            "The pet became short of breath and gagged after the first dose."
        ),
        reviewer_note=(
            "Serious clinical context included respiratory distress. "
            "Clarify the event timeline."
        ),
    )

    assert result.record_review_result.value == "documentation_incomplete"
    assert result.lot_batch_pattern_summary.value == "unavailable"
    assert result.inventory_inspection_result.value == "not_checked"
    assert result.api_reference_review_result.value == "not_needed"


def test_explicit_review_results_are_preserved() -> None:
    result = apply_review_summary_defaults(
        model_summary(),
        concern_text="The medication smelled different from prior bottles.",
        reviewer_note=(
            "Compounding-record review found no documented discrepancy. "
            "No additional quality complaints were identified for the lot. "
            "Available inventory was inspected and no odor concern was reproduced. "
            "The assessment incorporated USP guidance."
        ),
    )

    assert result.record_review_result.value == "no_discrepancy_found"
    assert result.lot_batch_pattern_summary.value == (
        "no_similar_batch_concerns_found"
    )
    assert result.inventory_inspection_result.value == "no_visual_concern_found"
    assert result.api_reference_review_result.value == (
        "external_reference_consulted"
    )


def test_worsening_bloodwork_requires_full_investigation() -> None:
    scope = infer_review_summary_scope(
        concern_text=(
            "How do we know each medication is uniform in the combined solution? "
            "The veterinarian is concerned because bloodwork is worsening."
        ),
        reviewer_note=(
            "The assessment incorporated USP guidance. "
            "Confirm shaking and resuspension technique."
        ),
    )

    assert scope is ReviewSummaryScope.FULL_INVESTIGATION


def test_reference_omission_defaults_to_not_needed() -> None:
    result = apply_review_summary_defaults(
        model_summary(),
        concern_text="The bottle appears short and may run out early.",
        reviewer_note=(
            "Compounding-record review found no documented discrepancy. "
            "No retained inventory was available for direct inspection."
        ),
    )

    assert result.api_reference_review_result.value == "not_needed"

def test_worksheet_review_is_treated_as_an_explicit_record_result() -> None:
    result = apply_review_summary_defaults(
        model_summary(),
        concern_text="Dog vomited after medication.",
        reviewer_note=(
            "Worksheet review found no discrepancy. "
            "No similar lot concerns. "
            "No inventory available. "
            "Dog recovered. No hospitalization."
        ),
    )

    assert result.record_review_result.value == "no_discrepancy_found"

def test_one_additional_lot_complaint_overrides_unavailable_model_output() -> None:
    summary = ReviewSummary(
        record_review_result="no_discrepancy_found",
        lot_batch_pattern_summary="unavailable",
        inventory_inspection_result="no_inventory_available",
        api_reference_review_result="not_needed",
        missing_information=[],
        evidence_limitations=[],
        severe_triggers_observed=[],
    )

    result = apply_review_summary_defaults(
        summary,
        concern_text=(
            "The pen clicks but pushes out less medication than before."
        ),
        reviewer_note=(
            "Compounding-record review found no documented discrepancy. "
            "One additional quality complaint was identified for the lot. "
            "No retained inventory was available for direct inspection."
        ),
    )

    assert result.lot_batch_pattern_summary.value == (
        "similar_concern_same_batch_found"
    )


def test_no_additional_lot_complaints_overrides_unavailable_model_output() -> None:
    summary = ReviewSummary(
        record_review_result="no_discrepancy_found",
        lot_batch_pattern_summary="unavailable",
        inventory_inspection_result="no_inventory_available",
        api_reference_review_result="not_needed",
        missing_information=[],
        evidence_limitations=[],
        severe_triggers_observed=[],
    )

    result = apply_review_summary_defaults(
        summary,
        concern_text="The medication smelled different.",
        reviewer_note=(
            "Compounding-record review found no documented discrepancy. "
            "No additional quality complaints were identified for the lot "
            "or source stock."
        ),
    )

    assert result.lot_batch_pattern_summary.value == (
        "no_similar_batch_concerns_found"
    )

