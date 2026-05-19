from __future__ import annotations

from app.checklist_models import IntakeChecklist
from app.schemas import (
    ConcernType,
    DerivedAssessment,
    DosageForm,
    EscalationTrigger,
    ExpectedStructuredOutput,
    FormalCategory,
    FormalClassification,
    FormalSubcategory,
    HandlingPath,
    IntakeSource,
    InvestigationRequirements,
    ProductContext,
    RawIntake,
    ResolutionOption,
    ReviewScope,
    ReviewSummary,
    RiskLane,
    Species,
    SubmitterRole,
    SubmissionPurpose,
)


def build_final_assessment(*, checklist: IntakeChecklist, review_summary: ReviewSummary) -> ExpectedStructuredOutput:
    concern_type = checklist.likely_concern_type or ConcernType.POSSIBLE_ADVERSE_DRUG_EVENT
    risk_lane = determine_final_risk_lane(checklist, review_summary)
    derived_assessment = build_derived_assessment(
        concern_type=concern_type,
        risk_lane=risk_lane,
        review_summary=review_summary,
    )

    return ExpectedStructuredOutput(
        raw_intake=RawIntake(
            intake_source=IntakeSource.QRE_GENERAL_QUESTION_FORM,
            submitter_role=SubmitterRole.UNKNOWN,
            submission_purpose=SubmissionPurpose.CUSTOMER_REPORTED_CONCERN,
            concern_narrative=checklist.concern_text,
            star_rating=None,
            review_text_present=None,
            submitter_selected_classification=None,
        ),
        product_context=infer_product_context(checklist.concern_text),
        investigation_requirements=InvestigationRequirements(
            record_review_required=True,
            lot_batch_review_required=True,
            inventory_inspection_required=None,
            trend_scan_required=None,
            customer_outreach_required=None,
            frontline_guidance_lookup_required=None,
            technical_services_response_required=None,
        ),
        review_summary=review_summary,
        derived_assessment=derived_assessment,
    )


def determine_final_risk_lane(checklist: IntakeChecklist, review_summary: ReviewSummary) -> RiskLane:
    text = " ".join(
        [
            checklist.concern_text,
            review_summary.customer_context_summary or "",
            " ".join(review_summary.missing_information),
            " ".join(review_summary.evidence_limitations),
        ]
    ).lower()

    severe_terms = {
        "death", "died", "hospitalized", "hospitalization", "legal", "lawsuit", "lawyer",
        "veterinarian alleges harm", "vet alleges harm", "contamination", "contaminated",
        "wrong medication", "wrong patient",
    }

    if contains_non_negated(text, severe_terms):
        return RiskLane.LIFE_THREATENING_OR_LEGAL

    if checklist.likely_concern_type in {ConcernType.FLAVOR_RELATED_VOMITING, ConcernType.POSSIBLE_ADVERSE_DRUG_EVENT}:
        return RiskLane.UNEXPECTED_NON_LIFE_THREATENING

    return checklist.likely_risk_lane or RiskLane.EXPECTED_SELF_LIMITING


def build_derived_assessment(*, concern_type: ConcernType, risk_lane: RiskLane, review_summary: ReviewSummary) -> DerivedAssessment:
    if concern_type == ConcernType.WRONG_PATIENT_OR_WRONG_MEDICATION:
        return DerivedAssessment(
            reviewer_assigned_classification=FormalClassification.QRE,
            reviewer_assigned_category=FormalCategory.DISPENSING_ERROR,
            reviewer_assigned_subcategory=FormalSubcategory.WRONG_MEDICATION,
            concern_type=concern_type,
            risk_lane=RiskLane.LIFE_THREATENING_OR_LEGAL,
            review_scope=ReviewScope.ESCALATION_REVIEW,
            escalation_triggers=[EscalationTrigger.WRONG_PATIENT_OR_WRONG_MEDICATION],
            handling_path=HandlingPath.LEADERSHIP_ESCALATION_BEFORE_RESOLUTION,
            resolution_review_required=True,
            resolution_options=[ResolutionOption.LEADERSHIP_DIRECTED_RESOLUTION, ResolutionOption.COUNSELING_OR_FOLLOW_UP],
            rationale="Possible wrong patient or wrong medication concerns are treated conservatively and require escalation before routine resolution.",
        )

    if risk_lane == RiskLane.LIFE_THREATENING_OR_LEGAL:
        return DerivedAssessment(
            reviewer_assigned_classification=FormalClassification.QRE,
            reviewer_assigned_category=FormalCategory.SUSPECTED_ADE,
            reviewer_assigned_subcategory=FormalSubcategory.FLAVOR_RELATED_ADE,
            concern_type=concern_type,
            risk_lane=risk_lane,
            review_scope=ReviewScope.ESCALATION_REVIEW,
            escalation_triggers=infer_escalation_triggers(review_summary),
            handling_path=HandlingPath.LEADERSHIP_ESCALATION_BEFORE_RESOLUTION,
            resolution_review_required=True,
            resolution_options=[ResolutionOption.LEADERSHIP_DIRECTED_RESOLUTION],
            rationale="A severe escalation trigger or high-risk concern requires escalation before routine resolution.",
        )

    if concern_type in {ConcernType.FLAVOR_RELATED_VOMITING, ConcernType.POSSIBLE_ADVERSE_DRUG_EVENT}:
        return DerivedAssessment(
            reviewer_assigned_classification=FormalClassification.QRE,
            reviewer_assigned_category=FormalCategory.SUSPECTED_ADE,
            reviewer_assigned_subcategory=FormalSubcategory.FLAVOR_RELATED_ADE,
            concern_type=concern_type,
            risk_lane=risk_lane,
            review_scope=ReviewScope.FULL_QUALITY_REVIEW,
            escalation_triggers=[],
            handling_path=HandlingPath.TECHNICAL_SERVICES_CUSTOMER_OUTREACH,
            resolution_review_required=True,
            resolution_options=[ResolutionOption.COUNSELING_OR_FOLLOW_UP, ResolutionOption.ALTERNATE_DOSAGE_FORM_DISCUSSION],
            rationale="Vomiting after administration is treated as a suspected adverse event. Without hospitalization, death, legal threat, contamination, wrong medication, or veterinarian allegation of harm, it supports follow-up rather than automatic leadership escalation.",
        )

    if concern_type == ConcernType.SYRINGE_OR_DEVICE_ISSUE:
        return DerivedAssessment(
            reviewer_assigned_classification=FormalClassification.QRE,
            reviewer_assigned_category=FormalCategory.EQUIPMENT_DEVICE_RELATED,
            reviewer_assigned_subcategory=FormalSubcategory.DEFECTIVE_DEVICE,
            concern_type=concern_type,
            risk_lane=risk_lane,
            review_scope=ReviewScope.FULL_QUALITY_REVIEW,
            escalation_triggers=[],
            handling_path=HandlingPath.TECHNICAL_SERVICES_CUSTOMER_OUTREACH,
            resolution_review_required=True,
            resolution_options=[ResolutionOption.REPLACEMENT_OR_RESHIP_REVIEW, ResolutionOption.COUNSELING_OR_FOLLOW_UP],
            rationale="A possible device or administration equipment issue supports quality review, customer follow-up, and possible replacement or reship review when no severe trigger is present.",
        )

    if concern_type == ConcernType.BUD_QUESTION:
        return DerivedAssessment(
            reviewer_assigned_classification=FormalClassification.GENERAL_QUESTION,
            reviewer_assigned_category=None,
            reviewer_assigned_subcategory=None,
            concern_type=concern_type,
            risk_lane=risk_lane,
            review_scope=ReviewScope.GUIDANCE_ONLY,
            escalation_triggers=[],
            handling_path=HandlingPath.RESPOND_TO_FRONTLINE_PHARMACIST,
            resolution_review_required=False,
            resolution_options=[],
            rationale="A BUD clarification without reported harm, defect, contamination, or dispensing error is handled as a guidance question requiring record-specific date fields.",
        )

    return DerivedAssessment(
        reviewer_assigned_classification=FormalClassification.QRE,
        reviewer_assigned_category=FormalCategory.MEDICATION_RELATED,
        reviewer_assigned_subcategory=FormalSubcategory.FLAVOR,
        concern_type=concern_type,
        risk_lane=risk_lane,
        review_scope=ReviewScope.FULL_QUALITY_REVIEW,
        escalation_triggers=[],
        handling_path=HandlingPath.TECHNICAL_SERVICES_CUSTOMER_OUTREACH,
        resolution_review_required=True,
        resolution_options=[ResolutionOption.COUNSELING_OR_FOLLOW_UP, ResolutionOption.ALTERNATE_DOSAGE_FORM_DISCUSSION],
        rationale="Routine flavor or palatability concerns without severe triggers support guidance, counseling, and possible alternate dosage form discussion after standard review checks.",
    )


def infer_product_context(concern_text: str) -> ProductContext:
    normalized = concern_text.lower()

    if "transdermal" in normalized or "pen" in normalized:
        dosage_form = DosageForm.TRANSDERMAL
    elif "liquid" in normalized or "oral" in normalized:
        dosage_form = DosageForm.ORAL_LIQUID
    else:
        dosage_form = DosageForm.UNKNOWN

    if "dog" in normalized:
        species = Species.DOG
    elif "cat" in normalized:
        species = Species.CAT
    else:
        species = Species.UNKNOWN

    flavor_or_attribute = None
    for flavor in ("chicken", "beef", "tuna", "flavor", "flavored"):
        if flavor in normalized:
            flavor_or_attribute = flavor
            break

    return ProductContext(
        species=species,
        dosage_form=dosage_form,
        product_placeholder=None,
        flavor_or_attribute=flavor_or_attribute,
        bud_present=None,
        batch_lot_present=None,
    )


def infer_escalation_triggers(review_summary: ReviewSummary) -> list[EscalationTrigger]:
    text = " ".join(
        [
            review_summary.customer_context_summary or "",
            " ".join(review_summary.missing_information),
            " ".join(review_summary.evidence_limitations),
        ]
    ).lower()

    triggers: list[EscalationTrigger] = []

    if "death" in text or "died" in text:
        triggers.append(EscalationTrigger.PET_DEATH)
    if "hospitalized" in text or "hospitalization" in text:
        triggers.append(EscalationTrigger.PET_HOSPITALIZATION)
    if "legal" in text or "lawsuit" in text or "lawyer" in text:
        triggers.append(EscalationTrigger.THREATENED_LEGAL_ACTION)
    if "vet alleges harm" in text or "veterinarian alleges harm" in text:
        triggers.append(EscalationTrigger.VETERINARIAN_ALLEGES_HARM_FROM_COMPOUND)
    if "contamination" in text or "contaminated" in text:
        triggers.append(EscalationTrigger.POSSIBLE_CONTAMINATION)
    if "wrong medication" in text or "wrong patient" in text:
        triggers.append(EscalationTrigger.WRONG_PATIENT_OR_WRONG_MEDICATION)

    return triggers

def contains_non_negated(text: str, terms: set[str]) -> bool:
    for term in terms:
        if term not in text:
            continue

        if f"no {term}" in text:
            continue

        if f"not {term}" in text:
            continue

        if f"without {term}" in text:
            continue

        return True

    return False