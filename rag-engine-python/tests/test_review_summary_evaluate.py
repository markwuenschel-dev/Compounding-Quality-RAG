from app.review_summary_evaluate import (
    evaluate_review_summary_extraction_cases,
)
from app.schemas import ReviewSummaryExtractionResult


def test_evaluation_reports_perfect_scores_for_exact_extractor() -> None:
    case = {
        "case_id": "case-1",
        "concern_text": "Dog vomited.",
        "reviewer_note": "No hospitalization.",
        "expected_review_summary": {
            "record_review_result": "no_discrepancy_found",
            "lot_batch_pattern_summary": "unavailable",
            "inventory_inspection_result": "not_checked",
            "customer_context_summary": None,
            "api_reference_review_result": "not_needed",
            "missing_information": ["Dose administered"],
            "evidence_limitations": [],
            "severe_triggers_observed": [],
        },
        "expected_unresolved_field_names": ["dose_administered"],
    }

    def extractor(
        concern_text: str,
        reviewer_note: str,
    ) -> ReviewSummaryExtractionResult:
        return ReviewSummaryExtractionResult.model_validate(
            {
                "review_summary": case["expected_review_summary"],
                "field_evidence": [],
                "unresolved_questions": [
                    {
                        "field_name": "dose_administered",
                        "question": "What dose was administered?",
                        "reason": "Dose context is missing.",
                        "decision_impact": ["review_scope"],
                    }
                ],
            }
        )

    result = evaluate_review_summary_extraction_cases(
        [case],
        extractor=extractor,
    )

    assert result["scalar_field_accuracy"] == 1.0
    assert result["missing_information_precision"] == 1.0
    assert result["missing_information_recall"] == 1.0
    assert result["severe_trigger_precision"] == 1.0
    assert result["severe_trigger_recall"] == 1.0
    assert result["unresolved_question_precision"] == 1.0
    assert result["unresolved_question_recall"] == 1.0


def test_evaluation_report_contains_actionable_failure_diagnostics() -> None:
    from app.review_summary_evaluate import format_evaluation_report

    case = {
        "case_id": "case-failure",
        "concern_text": "Dog vomited.",
        "reviewer_note": "Dose unknown and no hospitalization.",
        "expected_review_summary": {
            "record_review_result": "no_discrepancy_found",
            "lot_batch_pattern_summary": "unavailable",
            "inventory_inspection_result": "not_checked",
            "customer_context_summary": None,
            "api_reference_review_result": "not_needed",
            "missing_information": ["Exact dose administered"],
            "evidence_limitations": [],
            "severe_triggers_observed": [],
        },
        "expected_unresolved_field_names": ["dose_administered"],
    }

    def extractor(
        concern_text: str,
        reviewer_note: str,
    ) -> ReviewSummaryExtractionResult:
        return ReviewSummaryExtractionResult.model_validate(
            {
                "review_summary": {
                    "record_review_result": "documentation_incomplete",
                    "lot_batch_pattern_summary": "unavailable",
                    "inventory_inspection_result": "not_checked",
                    "customer_context_summary": None,
                    "api_reference_review_result": "not_needed",
                    "missing_information": ["Customer phone number"],
                    "evidence_limitations": [],
                    "severe_triggers_observed": ["pet_hospitalization"],
                },
                "field_evidence": [],
                "unresolved_questions": [
                    {
                        "field_name": "veterinarian_contact",
                        "question": "Was a veterinarian contacted?",
                        "reason": "Context missing.",
                        "decision_impact": ["handling_path"],
                    }
                ],
            }
        )

    result = evaluate_review_summary_extraction_cases(
        [case],
        extractor=extractor,
    )
    report = format_evaluation_report(result)

    assert "### case-failure" in report
    assert "`record_review_result`" in report
    assert "`no_discrepancy_found`" in report
    assert "`documentation_incomplete`" in report
    assert "False positives: `Customer phone number`" in report
    assert "False negatives: `Exact dose administered`" in report
    assert "False positives: `pet_hospitalization`" in report
    assert "False positives: `veterinarian_contact`" in report
    assert "False negatives: `dose_administered`" in report
