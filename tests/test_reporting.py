from pathlib import Path

from app.checklist import build_intake_checklist
from app.final_assessment import build_final_assessment
from app.reporting import (
    enum_value_or_none,
    enum_value_or_unknown,
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

    assert "COMPOUNDING QUALITY INTAKE CHECKLIST" in report
    assert "Likely concern type:" in report
    assert "Likely risk lane:" in report
    assert "Review checks:" in report
    assert "Missing information:" in report
    assert "Evidence:" in report
    assert "Limitations:" in report
    assert "does not access real compounding records" in report


def test_format_final_assessment_includes_structured_summary() -> None:
    checklist = make_checklist()
    output = build_final_assessment(
        checklist=checklist,
        review_summary=make_review_summary(),
    )

    report = format_final_assessment(output, checklist.evidence)

    assert "COMPOUNDING QUALITY FINAL CONSISTENCY SUMMARY" in report
    assert "Reviewer findings:" in report
    assert "Final structured assessment:" in report
    assert "Resolution options:" in report
    assert "Rationale:" in report
    assert "Evidence used:" in report
    assert "Human pharmacist review remains the final decision point." in report


def test_format_evidence_respects_max_items() -> None:
    checklist = make_checklist()

    lines = format_evidence(checklist.evidence, max_items=1)

    assert len(lines) == 1


def test_format_evidence_handles_empty_evidence() -> None:
    lines = format_evidence([])

    assert lines == ["- No evidence chunks were retrieved"]


def test_enum_value_helpers_handle_none_and_enums() -> None:
    assert enum_value_or_unknown(None) == "unknown"
    assert enum_value_or_unknown(RiskLane.EXPECTED_SELF_LIMITING) == "expected_self_limiting"

    assert enum_value_or_none(None) == "None"
    assert enum_value_or_none(RiskLane.UNEXPECTED_NON_LIFE_THREATENING) == "unexpected_non_life_threatening"