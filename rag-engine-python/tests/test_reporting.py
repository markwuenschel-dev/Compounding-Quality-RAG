from pathlib import Path

from app.checklist import build_intake_checklist
from app.final_assessment import build_final_assessment
from app.reporting import (
    humanize_or_none,
    humanize,
    format_evidence,
    format_final_assessment,
    format_intake_checklist,
)
from app.schemas import (
    ApiReferenceReviewResult,
    InventoryInspectionResult,
    LotBatchPatternSummary,
    RecordReviewResult,
    ReviewSummary,
    RiskLane,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "index" / "chunks.jsonl"


def make_checklist():
    return build_intake_checklist(
        "My dog received chicken flavored oral liquid and vomited once.",
        chunks_path=CHUNKS_PATH,
        top_k=3,
    )


def make_review_summary() -> ReviewSummary:
    return ReviewSummary(
        record_review_result=RecordReviewResult.NO_DISCREPANCY_FOUND,
        lot_batch_pattern_summary=LotBatchPatternSummary.NO_SIMILAR_BATCH_CONCERNS_FOUND,
        inventory_inspection_result=InventoryInspectionResult.NOT_CHECKED,
        customer_context_summary="Dog vomited once, recovered, no hospitalization reported.",
        api_reference_review_result=ApiReferenceReviewResult.NOT_NEEDED,
        missing_information=[],
        evidence_limitations=[],
    )


def test_format_intake_checklist_includes_manager_readable_sections() -> None:
    checklist = make_checklist()

    report = format_intake_checklist(checklist)

    assert "PHASE 1" in report
    assert "INTAKE CHECKLIST" in report
    assert "Demo boundary: synthetic proof of concept only" in report
    assert "INITIAL SUMMARY" in report
    assert "CONCERN RECEIVED" in report
    assert "INITIAL CLASSIFICATION" in report
    assert "EVIDENCE USED" in report
    assert "LIMITATIONS" in report
    assert "score=" not in report

    for item in checklist.review_checks:
        assert item.check_name in report

def test_format_final_assessment_debug_mode_shows_scores_and_matched_terms() -> None:
    checklist = make_checklist()
    output = build_final_assessment(
        checklist=checklist,
        review_summary=make_review_summary(),
    )

    report = format_final_assessment(output, checklist.evidence, debug=True)

    assert "score=" in report
    assert "matched_terms=" in report


def test_format_evidence_respects_max_items() -> None:
    checklist = make_checklist()

    lines = format_evidence(checklist.evidence, max_items=1)

    assert any(line.startswith("1. ") for line in lines)
    assert not any(line.startswith("2. ") for line in lines)


def test_format_evidence_hides_scores_by_default() -> None:
    checklist = make_checklist()

    lines = format_evidence(checklist.evidence, max_items=1)

    assert lines
    assert "score=" not in lines[0]


def test_format_evidence_handles_empty_evidence() -> None:
    lines = format_evidence([])

    assert lines == ["• No evidence chunks were retrieved"]


def test_enum_value_helpers_handle_none_and_enums() -> None:
    assert humanize(None) == "Unknown"
    assert humanize(RiskLane.EXPECTED_SELF_LIMITING) == "Expected self limiting"

    assert humanize_or_none(None) == "None"
    assert humanize_or_none(RiskLane.UNEXPECTED_NON_LIFE_THREATENING) == (
        "Unexpected non life threatening"
    )
