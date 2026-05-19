from pathlib import Path

from app.checklist import build_intake_checklist
from app.final_assessment import build_final_assessment, infer_product_context
from app.schemas import (
    ApiReferenceReviewResult,
    ConcernType,
    DosageForm,
    EscalationTrigger,
    FormalCategory,
    FormalClassification,
    FormalSubcategory,
    HandlingPath,
    InventoryInspectionResult,
    LotBatchPatternSummary,
    RecordReviewResult,
    ResolutionOption,
    ReviewScope,
    ReviewSummary,
    RiskLane,
    Species,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "index" / "chunks.jsonl"


def make_review_summary(
    *,
    customer_context_summary: str | None = "Vomited once, recovered, no hospitalization reported.",
) -> ReviewSummary:
    return ReviewSummary(
        record_review_result=RecordReviewResult.NO_DISCREPANCY_FOUND,
        lot_batch_pattern_summary=LotBatchPatternSummary.NO_SIMILAR_BATCH_CONCERNS_FOUND,
        inventory_inspection_result=InventoryInspectionResult.NOT_CHECKED,
        customer_context_summary=customer_context_summary,
        api_reference_review_result=ApiReferenceReviewResult.NOT_NEEDED,
        missing_information=[],
        evidence_limitations=[],
    )


def test_build_final_assessment_routes_flavor_related_vomiting_as_suspected_ade() -> None:
    checklist = build_intake_checklist(
        "My dog got chicken flavored oral liquid and vomited once.",
        chunks_path=CHUNKS_PATH,
        top_k=5,
    )

    output = build_final_assessment(
        checklist=checklist,
        review_summary=make_review_summary(),
    )

    assessment = output.derived_assessment

    assert assessment.reviewer_assigned_classification == FormalClassification.QRE
    assert assessment.reviewer_assigned_category == FormalCategory.SUSPECTED_ADE
    assert assessment.reviewer_assigned_subcategory == FormalSubcategory.FLAVOR_RELATED_ADE
    assert assessment.concern_type == ConcernType.FLAVOR_RELATED_VOMITING
    assert assessment.risk_lane == RiskLane.UNEXPECTED_NON_LIFE_THREATENING
    assert assessment.review_scope == ReviewScope.FULL_QUALITY_REVIEW
    assert assessment.handling_path == HandlingPath.TECHNICAL_SERVICES_CUSTOMER_OUTREACH
    assert ResolutionOption.COUNSELING_OR_FOLLOW_UP in assessment.resolution_options


def test_build_final_assessment_escalates_hospitalization() -> None:
    checklist = build_intake_checklist(
        "Dog vomited after chicken flavored oral liquid.",
        chunks_path=CHUNKS_PATH,
        top_k=5,
    )

    output = build_final_assessment(
        checklist=checklist,
        review_summary=make_review_summary(
            customer_context_summary="The dog was hospitalized after administration."
        ),
    )

    assessment = output.derived_assessment

    assert assessment.risk_lane == RiskLane.LIFE_THREATENING_OR_LEGAL
    assert assessment.review_scope == ReviewScope.ESCALATION_REVIEW
    assert assessment.handling_path == HandlingPath.LEADERSHIP_ESCALATION_BEFORE_RESOLUTION
    assert EscalationTrigger.PET_HOSPITALIZATION in assessment.escalation_triggers


def test_build_final_assessment_handles_bud_question_as_general_question() -> None:
    checklist = build_intake_checklist(
        "Frontline pharmacist asks whether the oral liquid product is within BUD.",
        chunks_path=CHUNKS_PATH,
        top_k=5,
    )

    output = build_final_assessment(
        checklist=checklist,
        review_summary=make_review_summary(customer_context_summary="BUD field review requested."),
    )

    assessment = output.derived_assessment

    assert assessment.reviewer_assigned_classification == FormalClassification.GENERAL_QUESTION
    assert assessment.reviewer_assigned_category is None
    assert assessment.reviewer_assigned_subcategory is None
    assert assessment.concern_type == ConcernType.BUD_QUESTION
    assert assessment.handling_path == HandlingPath.RESPOND_TO_FRONTLINE_PHARMACIST
    assert assessment.resolution_review_required is False
    assert assessment.resolution_options == []


def test_build_final_assessment_handles_transdermal_device_issue() -> None:
    checklist = build_intake_checklist(
        "The transdermal pen leaks after two clicks and has air bubbles.",
        chunks_path=CHUNKS_PATH,
        top_k=5,
    )

    output = build_final_assessment(
        checklist=checklist,
        review_summary=make_review_summary(customer_context_summary="No harm reported."),
    )

    assessment = output.derived_assessment

    assert output.product_context.dosage_form == DosageForm.TRANSDERMAL
    assert assessment.reviewer_assigned_category == FormalCategory.EQUIPMENT_DEVICE_RELATED
    assert assessment.reviewer_assigned_subcategory == FormalSubcategory.DEFECTIVE_DEVICE
    assert assessment.concern_type == ConcernType.SYRINGE_OR_DEVICE_ISSUE
    assert ResolutionOption.REPLACEMENT_OR_RESHIP_REVIEW in assessment.resolution_options


def test_build_final_assessment_handles_wrong_medication_conservatively() -> None:
    checklist = build_intake_checklist(
        "Possible wrong medication for wrong patient.",
        chunks_path=CHUNKS_PATH,
        top_k=5,
    )

    output = build_final_assessment(
        checklist=checklist,
        review_summary=make_review_summary(customer_context_summary="Severity not yet known."),
    )

    assessment = output.derived_assessment

    assert assessment.risk_lane == RiskLane.LIFE_THREATENING_OR_LEGAL
    assert assessment.handling_path == HandlingPath.LEADERSHIP_ESCALATION_BEFORE_RESOLUTION
    assert EscalationTrigger.WRONG_PATIENT_OR_WRONG_MEDICATION in assessment.escalation_triggers


def test_infer_product_context_detects_species_and_dosage_form() -> None:
    product_context = infer_product_context(
        "My dog received chicken flavored oral liquid."
    )

    assert product_context.species == Species.DOG
    assert product_context.dosage_form == DosageForm.ORAL_LIQUID
    assert product_context.flavor_or_attribute == "chicken"