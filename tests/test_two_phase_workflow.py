from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from app.checklist import build_intake_checklist
from app.final_assessment import build_final_assessment
from app.refusal import evaluate_refusal
from app.reporting import format_final_assessment, format_intake_checklist
from app.schemas import (
    ApiReferenceReviewResult,
    ConcernType,
    DosageForm,
    EscalationTrigger,
    FormalCategory,
    FormalClassification,
    HandlingPath,
    InventoryInspectionResult,
    LotBatchPatternSummary,
    RecordReviewResult,
    ResolutionOption,
    ReviewSummary,
    RiskLane,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "index" / "chunks.jsonl"


@dataclass(frozen=True)
class TwoPhaseCase:
    case_id: str
    concern_text: str
    review_summary: ReviewSummary
    expected_concern_type: ConcernType
    expected_risk_lane: RiskLane
    expected_handling_path: HandlingPath
    expected_classification: FormalClassification
    expected_category: FormalCategory | None = None
    expected_dosage_form: DosageForm | None = None
    expected_resolution_required: bool | None = None
    expected_resolution_option: ResolutionOption | None = None
    expected_escalation_trigger: EscalationTrigger | None = None


def make_review_summary(
    *,
    record_review_result: RecordReviewResult = RecordReviewResult.NO_DISCREPANCY_FOUND,
    lot_batch_pattern_summary: LotBatchPatternSummary = LotBatchPatternSummary.NO_SIMILAR_BATCH_CONCERNS_FOUND,
    inventory_inspection_result: InventoryInspectionResult = InventoryInspectionResult.NOT_CHECKED,
    api_reference_review_result: ApiReferenceReviewResult = ApiReferenceReviewResult.NOT_NEEDED,
    customer_context_summary: str | None = None,
    severe_triggers_observed: list[EscalationTrigger] | None = None,
    missing_information: list[str] | None = None,
    evidence_limitations: list[str] | None = None,
) -> ReviewSummary:
    return ReviewSummary(
        record_review_result=record_review_result,
        lot_batch_pattern_summary=lot_batch_pattern_summary,
        inventory_inspection_result=inventory_inspection_result,
        api_reference_review_result=api_reference_review_result,
        customer_context_summary=customer_context_summary,
        severe_triggers_observed=severe_triggers_observed or [],
        missing_information=missing_information or [],
        evidence_limitations=evidence_limitations or [],
    )


TWO_PHASE_CASES = [
    TwoPhaseCase(
        case_id="flavor_refusal",
        concern_text="Customer reports dog refuses the chicken flavored oral liquid.",
        review_summary=make_review_summary(
            customer_context_summary=(
                "Dog refused the flavored oral liquid. No severe escalation trigger "
                "was observed by the reviewer."
            ),
            missing_information=["Whether alternate flavor or dosage form is preferred."],
        ),
        expected_concern_type=ConcernType.PET_REFUSED_FLAVOR,
        expected_risk_lane=RiskLane.EXPECTED_SELF_LIMITING,
        expected_handling_path=HandlingPath.TECHNICAL_SERVICES_CUSTOMER_OUTREACH,
        expected_classification=FormalClassification.QRE,
        expected_category=FormalCategory.MEDICATION_RELATED,
        expected_dosage_form=DosageForm.ORAL_LIQUID,
        expected_resolution_required=True,
        expected_resolution_option=ResolutionOption.COUNSELING_OR_FOLLOW_UP,
    ),
    TwoPhaseCase(
        case_id="flavor_related_vomiting",
        concern_text=(
            "My dog received chicken flavored oral liquid, ran around frantically, "
            "and vomited once about 10 minutes after administration."
        ),
        review_summary=make_review_summary(
            customer_context_summary=(
                "Dog vomited once about 10 minutes after administration and recovered. "
                "Reviewer observed no severe escalation trigger."
            ),
            missing_information=["Exact dose administered by customer."],
            evidence_limitations=["Inventory was not available to inspect."],
        ),
        expected_concern_type=ConcernType.FLAVOR_RELATED_VOMITING,
        expected_risk_lane=RiskLane.UNEXPECTED_NON_LIFE_THREATENING,
        expected_handling_path=HandlingPath.TECHNICAL_SERVICES_CUSTOMER_OUTREACH,
        expected_classification=FormalClassification.QRE,
        expected_category=FormalCategory.SUSPECTED_ADE,
        expected_dosage_form=DosageForm.ORAL_LIQUID,
        expected_resolution_required=True,
        expected_resolution_option=ResolutionOption.COUNSELING_OR_FOLLOW_UP,
    ),
    TwoPhaseCase(
        case_id="bud_question",
        concern_text=(
            "Frontline pharmacist asks whether the oral liquid product is within "
            "the beyond use date BUD."
        ),
        review_summary=make_review_summary(
            inventory_inspection_result=InventoryInspectionResult.NOT_APPLICABLE,
            customer_context_summary=(
                "Frontline pharmacist requested BUD clarification. Reviewer observed "
                "no severe escalation trigger."
            ),
            missing_information=[
                "Preparation date.",
                "Assigned beyond-use date.",
                "Dispense or review date.",
            ],
        ),
        expected_concern_type=ConcernType.BUD_QUESTION,
        expected_risk_lane=RiskLane.EXPECTED_SELF_LIMITING,
        expected_handling_path=HandlingPath.RESPOND_TO_FRONTLINE_PHARMACIST,
        expected_classification=FormalClassification.GENERAL_QUESTION,
        expected_category=None,
        expected_dosage_form=DosageForm.ORAL_LIQUID,
        expected_resolution_required=False,
    ),
    TwoPhaseCase(
        case_id="transdermal_device_issue",
        concern_text=(
            "Customer reports the transdermal pen leaks from the bottom, has air "
            "bubbles, and does not dispense after two clicks."
        ),
        review_summary=make_review_summary(
            customer_context_summary=(
                "Customer reports the transdermal pen may not be dispensing correctly. "
                "Reviewer observed no severe escalation trigger."
            ),
            evidence_limitations=["Device was not physically inspected by this tool."],
        ),
        expected_concern_type=ConcernType.SYRINGE_OR_DEVICE_ISSUE,
        expected_risk_lane=RiskLane.EXPECTED_SELF_LIMITING,
        expected_handling_path=HandlingPath.TECHNICAL_SERVICES_CUSTOMER_OUTREACH,
        expected_classification=FormalClassification.QRE,
        expected_category=FormalCategory.EQUIPMENT_DEVICE_RELATED,
        expected_dosage_form=DosageForm.TRANSDERMAL,
        expected_resolution_required=True,
        expected_resolution_option=ResolutionOption.REPLACEMENT_OR_RESHIP_REVIEW,
    ),
    TwoPhaseCase(
        case_id="wrong_patient_wrong_medication",
        concern_text=(
            "Possible wrong medication was dispensed for the wrong patient. "
            "Severity is not yet known."
        ),
        review_summary=make_review_summary(
            record_review_result=RecordReviewResult.DOCUMENTATION_DISCREPANCY_FOUND,
            lot_batch_pattern_summary=LotBatchPatternSummary.NOT_APPLICABLE,
            inventory_inspection_result=InventoryInspectionResult.NOT_APPLICABLE,
            customer_context_summary=(
                "Reviewer confirmed possible wrong patient or wrong medication issue."
            ),
            severe_triggers_observed=[
                EscalationTrigger.WRONG_PATIENT_OR_WRONG_MEDICATION
            ],
            missing_information=[
                "Whether the medication was delivered.",
                "Whether the medication was administered.",
                "Whether veterinarian or customer was contacted.",
            ],
        ),
        expected_concern_type=ConcernType.WRONG_PATIENT_OR_WRONG_MEDICATION,
        expected_risk_lane=RiskLane.LIFE_THREATENING_OR_LEGAL,
        expected_handling_path=HandlingPath.LEADERSHIP_ESCALATION_BEFORE_RESOLUTION,
        expected_classification=FormalClassification.QRE,
        expected_category=FormalCategory.DISPENSING_ERROR,
        expected_resolution_required=True,
        expected_resolution_option=ResolutionOption.LEADERSHIP_DIRECTED_RESOLUTION,
        expected_escalation_trigger=EscalationTrigger.WRONG_PATIENT_OR_WRONG_MEDICATION,
    ),
]


@pytest.mark.parametrize("case", TWO_PHASE_CASES, ids=lambda case: case.case_id)
def test_all_five_cases_run_through_same_two_phase_workflow(case: TwoPhaseCase) -> None:
    checklist = build_intake_checklist(case.concern_text, chunks_path=CHUNKS_PATH, top_k=5)
    final_output = build_final_assessment(
        checklist=checklist,
        review_summary=case.review_summary,
    )

    assessment = final_output.derived_assessment

    assert checklist.concern_text == case.concern_text
    assert checklist.evidence
    assert checklist.review_checks
    assert checklist.missing_information
    assert checklist.escalation_triggers_to_rule_out

    assert final_output.raw_intake.concern_narrative == case.concern_text
    assert assessment.concern_type == case.expected_concern_type
    assert assessment.risk_lane == case.expected_risk_lane
    assert assessment.handling_path == case.expected_handling_path
    assert assessment.reviewer_assigned_classification == case.expected_classification
    assert assessment.reviewer_assigned_category == case.expected_category

    if case.expected_dosage_form is not None:
        assert final_output.product_context.dosage_form == case.expected_dosage_form

    if case.expected_resolution_required is not None:
        assert assessment.resolution_review_required is case.expected_resolution_required

    if case.expected_resolution_option is not None:
        assert case.expected_resolution_option in assessment.resolution_options

    if case.expected_escalation_trigger is not None:
        assert case.expected_escalation_trigger in assessment.escalation_triggers


@pytest.mark.parametrize("case", TWO_PHASE_CASES, ids=lambda case: case.case_id)
def test_all_five_cases_generate_manager_readable_reports(case: TwoPhaseCase) -> None:
    checklist = build_intake_checklist(case.concern_text, chunks_path=CHUNKS_PATH, top_k=5)
    final_output = build_final_assessment(
        checklist=checklist,
        review_summary=case.review_summary,
    )

    checklist_report = format_intake_checklist(checklist)
    final_report = format_final_assessment(final_output, checklist.evidence)

    assert "COMPOUNDING QUALITY INTAKE CHECKLIST" in checklist_report
    assert "SYNTHETIC PROOF OF CONCEPT" in checklist_report
    assert "Initial review takeaway:" in checklist_report
    assert "What should be checked:" in checklist_report
    assert "Evidence used for checklist:" in checklist_report

    assert "COMPOUNDING QUALITY FINAL CONSISTENCY SUMMARY" in final_report
    assert "SYNTHETIC PROOF OF CONCEPT" in final_report
    assert "Final review takeaway:" in final_report
    assert "Recommended review disposition:" in final_report
    assert "Human pharmacist review remains the final decision point." in final_report


@pytest.mark.parametrize("case", TWO_PHASE_CASES, ids=lambda case: case.case_id)
def test_two_phase_reports_hide_debug_scores_by_default(case: TwoPhaseCase) -> None:
    checklist = build_intake_checklist(case.concern_text, chunks_path=CHUNKS_PATH, top_k=5)
    final_output = build_final_assessment(
        checklist=checklist,
        review_summary=case.review_summary,
    )

    checklist_report = format_intake_checklist(checklist)
    final_report = format_final_assessment(final_output, checklist.evidence)

    assert "score=" not in checklist_report
    assert "matched_terms=" not in checklist_report
    assert "score=" not in final_report
    assert "matched_terms=" not in final_report


@pytest.mark.parametrize("case", TWO_PHASE_CASES, ids=lambda case: case.case_id)
def test_two_phase_reports_can_show_debug_evidence_when_requested(case: TwoPhaseCase) -> None:
    checklist = build_intake_checklist(case.concern_text, chunks_path=CHUNKS_PATH, top_k=5)
    final_output = build_final_assessment(
        checklist=checklist,
        review_summary=case.review_summary,
    )

    checklist_report = format_intake_checklist(checklist, debug=True)
    final_report = format_final_assessment(final_output, checklist.evidence, debug=True)

    assert "score=" in checklist_report
    assert "matched_terms=" in checklist_report
    assert "score=" in final_report
    assert "matched_terms=" in final_report


def test_refusal_short_circuits_real_record_access_before_two_phase_workflow() -> None:
    concern_text = (
        "Can you look at the real compounding record and tell me if this batch "
        "had the same vomiting complaints?"
    )

    refusal = evaluate_refusal(concern_text)

    assert refusal.refused is True
    assert refusal.message is not None
    assert "does not access real compounding records" in refusal.message
    assert "synthetic" in refusal.message.lower()


def test_refusal_short_circuits_external_reference_request_before_two_phase_workflow() -> None:
    concern_text = (
        "Can you check Plumb's and tell me whether this medication causes "
        "vomiting in dogs?"
    )

    refusal = evaluate_refusal(concern_text)

    assert refusal.refused is True
    assert refusal.message is not None
    assert "external drug reference" in refusal.message.lower()
    assert "Do not infer or fabricate" in refusal.message
