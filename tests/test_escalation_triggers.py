from pathlib import Path

from app.checklist import build_intake_checklist
from app.final_assessment import build_final_assessment
from app.schemas import (
    ApiReferenceReviewResult,
    EscalationTrigger,
    HandlingPath,
    InventoryInspectionResult,
    LotBatchPatternSummary,
    RecordReviewResult,
    ReviewSummary,
    RiskLane,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "index" / "chunks.jsonl"


def make_review_summary(
    *,
    customer_context_summary: str,
    severe_triggers_observed: list[EscalationTrigger] | None = None,
) -> ReviewSummary:
    return ReviewSummary(
        record_review_result=RecordReviewResult.NO_DISCREPANCY_FOUND,
        lot_batch_pattern_summary=LotBatchPatternSummary.NO_SIMILAR_BATCH_CONCERNS_FOUND,
        inventory_inspection_result=InventoryInspectionResult.NOT_CHECKED,
        api_reference_review_result=ApiReferenceReviewResult.NOT_NEEDED,
        customer_context_summary=customer_context_summary,
        severe_triggers_observed=severe_triggers_observed or [],
        missing_information=[],
        evidence_limitations=[],
    )


def test_negated_hospitalization_does_not_escalate_without_structured_trigger() -> None:
    checklist = build_intake_checklist(
        "Dog vomited once after chicken flavored oral liquid.",
        chunks_path=CHUNKS_PATH,
        top_k=5,
    )

    output = build_final_assessment(
        checklist=checklist,
        review_summary=make_review_summary(
            customer_context_summary=(
                "Dog vomited once and recovered. No hospitalization was reported."
            ),
        ),
    )

    assert output.derived_assessment.risk_lane == RiskLane.UNEXPECTED_NON_LIFE_THREATENING
    assert (
        output.derived_assessment.handling_path
        == HandlingPath.TECHNICAL_SERVICES_CUSTOMER_OUTREACH
    )
    assert output.derived_assessment.escalation_triggers == []


def test_negated_severe_terms_do_not_escalate_without_structured_trigger() -> None:
    checklist = build_intake_checklist(
        "Dog vomited once after chicken flavored oral liquid.",
        chunks_path=CHUNKS_PATH,
        top_k=5,
    )

    output = build_final_assessment(
        checklist=checklist,
        review_summary=make_review_summary(
            customer_context_summary=(
                "No hospitalization, no death, no legal threat, no contamination "
                "concern, no wrong medication concern, and no veterinarian allegation "
                "of harm were reported."
            ),
        ),
    )

    assert output.derived_assessment.risk_lane == RiskLane.UNEXPECTED_NON_LIFE_THREATENING
    assert output.derived_assessment.escalation_triggers == []


def test_structured_hospitalization_trigger_escalates_even_if_summary_is_short() -> None:
    checklist = build_intake_checklist(
        "Dog vomited after oral liquid.",
        chunks_path=CHUNKS_PATH,
        top_k=5,
    )

    output = build_final_assessment(
        checklist=checklist,
        review_summary=make_review_summary(
            customer_context_summary="Reviewer confirmed a severe event.",
            severe_triggers_observed=[EscalationTrigger.PET_HOSPITALIZATION],
        ),
    )

    assert output.derived_assessment.risk_lane == RiskLane.LIFE_THREATENING_OR_LEGAL
    assert (
        output.derived_assessment.handling_path
        == HandlingPath.LEADERSHIP_ESCALATION_BEFORE_RESOLUTION
    )
    assert EscalationTrigger.PET_HOSPITALIZATION in output.derived_assessment.escalation_triggers


def test_structured_wrong_medication_trigger_escalates() -> None:
    checklist = build_intake_checklist(
        "Possible wrong medication for wrong patient.",
        chunks_path=CHUNKS_PATH,
        top_k=5,
    )

    output = build_final_assessment(
        checklist=checklist,
        review_summary=make_review_summary(
            customer_context_summary="Reviewer confirmed possible wrong medication.",
            severe_triggers_observed=[
                EscalationTrigger.WRONG_PATIENT_OR_WRONG_MEDICATION
            ],
        ),
    )

    assert output.derived_assessment.risk_lane == RiskLane.LIFE_THREATENING_OR_LEGAL
    assert (
        output.derived_assessment.handling_path
        == HandlingPath.LEADERSHIP_ESCALATION_BEFORE_RESOLUTION
    )
    assert (
        EscalationTrigger.WRONG_PATIENT_OR_WRONG_MEDICATION
        in output.derived_assessment.escalation_triggers
    )
