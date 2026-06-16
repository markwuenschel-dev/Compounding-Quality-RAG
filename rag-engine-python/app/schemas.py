from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictBaseModel(BaseModel):
    """Project base model: reject unknown fields so schema drift fails loudly."""

    model_config = ConfigDict(extra="forbid")


class SourceType(StrEnum):
    SOP = "sop"
    SYNTHETIC_INQUIRY = "synthetic_inquiry"
    SYNTHETIC_API_REFERENCE = "synthetic_api_reference"
    EVAL_QUESTION = "eval_question"


class IntakeSource(StrEnum):
    QRE_GENERAL_QUESTION_FORM = "qre_general_question_form"
    CUSTOMER_REVIEW = "customer_review"


class SubmitterRole(StrEnum):
    FRONTLINE_PHARMACIST = "frontline_pharmacist"
    CUSTOMER = "customer"
    CUSTOMER_CARE = "customer_care"
    CUSTOMER_REVIEW_SYSTEM = "customer_review_system"
    TECHNICAL_SERVICES = "technical_services"
    OPERATIONS_LEADERSHIP = "operations_leADErship"
    OTHER = "other"
    UNKNOWN = "unknown"


class SubmissionPurpose(StrEnum):
    CUSTOMER_REPORTED_CONCERN = "customer_reported_concern"
    FRONTLINE_PHARMACIST_QUESTION = "frontline_pharmacist_question"
    DOCUMENTATION_UPDATE = "documentation_update"
    ESCALATION_REQUEST = "escalation_request"
    CUSTOMER_REVIEW_FOLLOWUP = "customer_review_followup"
    OTHER = "other"


class FormalClassification(StrEnum):
    QRE = "QRE"
    GENERAL_QUESTION = "general_question"


class FormalCategory(StrEnum):
    CUSTOMER_SERVICE_RELATED = "customer_service_related"
    EQUIPMENT_DEVICE_RELATED = "equipment_device_related"
    MEDICATION_RELATED = "medication_related"
    SUSPECTED_ADE = "suspected_ADE"
    DISPENSING_ERROR = "dispensing_error"


class FormalSubcategory(StrEnum):
    CUSTOMER_EXPERIENCE = "customer_experience"
    AUTOSHIP_ISSUE = "autoship_issue"
    CLICK_TO_DELIVERY = "click_to_delivery"
    PACKAGING = "packaging"
    PRICING = "pricing"

    MISSING_EQUIPMENT = "missing_equipment"
    DEFECTIVE_DEVICE = "defective_device"
    SYRINGE_ISSUE = "syringe_issue"

    FLAVOR = "flavor"
    BUD = "bud"
    FORMULATION = "formulation"
    PACKAGE_SIZE = "package_size"
    EFFICACY = "efficacy"
    DAYS_SUPPLY = "days_supply"

    SUSPECTED_ADE = "suspected_ADE"
    FLAVOR_RELATED_ADE = "flavor_related_ADE"

    WRONG_QUANTITY = "wrong_quantity"
    WRONG_PATIENT = "wrong_patient"
    WRONG_MEDICATION = "wrong_medication"
    WRONG_DIRECTIONS = "wrong_directions"
    MISSING_ITEM = "missing_item"
    COMPOUNDING_ERROR = "compounding_error"
    LABELING_ERROR = "labeling_error"


class ConcernType(StrEnum):
    PET_REFUSED_FLAVOR = "pet_refused_flavor"
    SMELL_CONCERN = "smell_concern"
    VISCOSITY_OR_THICKNESS_CONCERN = "viscosity_or_thickness_concern"
    COLOR_CHANGE = "color_change"
    EFFICACY_CONCERN = "efficacy_concern"
    POSSIBLE_ADVERSE_DRUG_EVENT = "possible_adverse_drug_event"
    FLAVOR_RELATED_VOMITING = "flavor_related_vomiting"
    INGREDIENT_PRESENCE_QUESTION = "ingredient_presence_question"
    ORAL_LIQUID_SHORTAGE = "oral_liquid_shortage"
    DAYS_SUPPLY_QUESTION = "days_supply_question"
    BUD_QUESTION = "bud_question"
    TEMPERATURE_EXCURSION_QUESTION = "temperature_excursion_question"
    LIMITED_GUIDANCE_SPECIALTY_COMPOUND_QUESTION = "limited_guidance_specialty_compound_question"
    SYRINGE_OR_DEVICE_ISSUE = "syringe_or_device_issue"
    PACKAGE_DAMAGE_OR_LEAKAGE = "package_damage_or_leakage"
    BROKEN_TABLET_OR_CAPSULE_DAMAGE = "broken_tablet_or_capsule_damage"
    LABELING_ISSUE = "labeling_issue"
    POSSIBLE_DISPENSING_ERROR = "possible_dispensing_error"
    WRONG_PATIENT_OR_WRONG_MEDICATION = "wrong_patient_or_wrong_medication"
    POSSIBLE_CONTAMINATION = "possible_contamination"
    VETERINARIAN_ALLEGES_HARM = "veterinarian_alleges_harm"
    PET_HOSPITALIZED = "pet_hospitalized"
    PET_DEATH = "pet_death"
    THREATENED_LEGAL_ACTION = "threatened_legal_action"


class RiskLane(StrEnum):
    EXPECTED_SELF_LIMITING = "expected_self_limiting"
    UNEXPECTED_NON_LIFE_THREATENING = "unexpected_non_life_threatening"
    LIFE_THREATENING_OR_LEGAL = "life_threatening_or_legal"


class ReviewScope(StrEnum):
    FULL_QUALITY_REVIEW = "full_quality_review"
    CUSTOMER_REVIEW_RECORD_CHECK = "customer_review_record_check"
    GUIDANCE_ONLY = "guidance_only"
    ESCALATION_REVIEW = "escalation_review"
    INSUFFICIENT_INFORMATION = "insufficient_information"


class RecordReviewResult(StrEnum):
    NO_DISCREPANCY_FOUND = "no_discrepancy_found"
    DOCUMENTATION_INCOMPLETE = "documentation_incomplete"
    DOCUMENTATION_DISCREPANCY_FOUND = "documentation_discrepancy_found"
    NOT_APPLICABLE = "not_applicable"


class LotBatchPatternSummary(StrEnum):
    NO_SIMILAR_BATCH_CONCERNS_FOUND = "no_similar_batch_concerns_found"
    SIMILAR_CONCERN_SAME_BATCH_FOUND = "similar_concern_same_batch_found"
    SIMILAR_CONCERN_SAME_MEDICATION_DOSAGE_FORM_FOUND = "similar_concern_same_medication_dosage_form_found"
    TREND_THRESHOLD_MET = "trend_threshold_met"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


class InventoryInspectionResult(StrEnum):
    NO_INVENTORY_AVAILABLE = "no_inventory_available"
    NO_VISUAL_CONCERN_FOUND = "no_visual_concern_found"
    VISUAL_CONCERN_FOUND = "visual_concern_found"
    NOT_CHECKED = "not_checked"
    NOT_APPLICABLE = "not_applicable"


class ApiReferenceReviewResult(StrEnum):
    NOT_NEEDED = "not_needed"
    SYNTHETIC_REFERENCE_CONSULTED = "synthetic_reference_consulted"
    EXTERNAL_REFERENCE_CONSULTED = "external_reference_consulted"
    EXTERNAL_REFERENCE_NEEDED = "external_reference_needed"
    NOT_SUPPORTED_BY_PUBLIC_CORPUS = "not_supported_by_public_corpus"


class HandlingPath(StrEnum):
    DOCUMENT_ONLY_NO_ACTION = "document_only_no_action"
    DELEGATE_TO_FRONTLINE_PHARMACIST = "delegate_to_frontline_pharmacist"
    RESPOND_TO_FRONTLINE_PHARMACIST = "respond_to_frontline_pharmacist"
    TECHNICAL_SERVICES_CUSTOMER_OUTREACH = "technical_services_customer_outreach"
    RECORD_REVIEW_THEN_DOCUMENT = "record_review_then_document"
    INVESTIGATE_TO_RESOLUTION = "investigate_to_resolution"
    FLAG_LEADERSHIP_DURING_INVESTIGATION = "flag_leADErship_during_investigation"
    LEADERSHIP_ESCALATION_BEFORE_RESOLUTION = "leADErship_escalation_before_resolution"
    INSUFFICIENT_INFORMATION = "insufficient_information"


class ResolutionOption(StrEnum):
    REPLACEMENT_OR_RESHIP_REVIEW = "replacement_or_reship_review"
    REFUND_OR_CONCESSION_REVIEW = "refund_or_concession_review"
    ALTERNATE_DOSAGE_FORM_DISCUSSION = "alternate_dosage_form_discussion"
    COUNSELING_OR_FOLLOW_UP = "counseling_or_follow_up"
    LEADERSHIP_DIRECTED_RESOLUTION = "leADErship_directed_resolution"
    NO_CUSTOMER_FACING_RESOLUTION = "no_customer_facing_resolution"


class EscalationTrigger(StrEnum):
    PET_DEATH = "pet_death"
    PET_HOSPITALIZATION = "pet_hospitalization"
    THREATENED_LEGAL_ACTION = "threatened_legal_action"
    VETERINARIAN_ALLEGES_HARM_FROM_COMPOUND = "veterinarian_alleges_harm_from_compound"
    POSSIBLE_CONTAMINATION = "possible_contamination"
    WRONG_PATIENT_OR_WRONG_MEDICATION = "wrong_patient_or_wrong_medication"
    REPEAT_ISSUE_SAME_LOT_OR_BATCH_WITH_CONDITIONS = "repeat_issue_same_lot_or_batch_with_conditions"
    RARE_REGULATORY_OR_COMPLIANCE_CONCERN = "rare_regulatory_or_compliance_concern"


class Species(StrEnum):
    CAT = "cat"
    DOG = "dog"
    HORSE = "horse"
    OTHER = "other"
    UNKNOWN = "unknown"


class DosageForm(StrEnum):
    ORAL_LIQUID = "oral_liquid"
    CAPSULE = "capsule"
    TABLET = "tablet"
    TRANSDERMAL = "transdermal"
    CHEWABLE = "chewable"
    POWDER = "powder"
    OPHTHALMIC = "ophthalmic"
    ORAL_PASTE = "oral_paste"
    TOPICAL = "topical"
    OTHER = "other"
    UNKNOWN = "unknown"


class SopDocument(StrictBaseModel):
    document_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    version: str = Field(min_length=1)
    effective_date: str = Field(min_length=1)
    process_area: str = Field(min_length=1)
    source_type: Literal[SourceType.SOP] = SourceType.SOP
    synthetic: Literal[True] = True
    body_text: str = Field(min_length=1)


class RawIntake(StrictBaseModel):
    intake_source: IntakeSource
    submitter_role: SubmitterRole
    submission_purpose: SubmissionPurpose
    concern_narrative: str = Field(min_length=1)
    star_rating: int | None = Field(default=None, ge=1, le=5)
    review_text_present: bool | None = None
    submitter_selected_classification: FormalClassification | None = None

    @model_validator(mode="after")
    def validate_customer_review_fields(self) -> Self:
        if self.intake_source == IntakeSource.CUSTOMER_REVIEW:
            if self.star_rating is None:
                raise ValueError("customer_review records must include star_rating")
            if self.review_text_present is None:
                raise ValueError("customer_review records must include review_text_present")
        else:
            if self.star_rating is not None:
                raise ValueError("star_rating should only be used for customer_review records")
            if self.review_text_present is not None:
                raise ValueError("review_text_present should only be used for customer_review records")
        return self


class ProductContext(StrictBaseModel):
    species: Species = Species.UNKNOWN
    dosage_form: DosageForm = DosageForm.UNKNOWN
    product_placeholder: str | None = None
    flavor_or_attribute: str | None = None
    bud_present: bool | None = None
    batch_lot_present: bool | None = None


class InvestigationRequirements(StrictBaseModel):
    record_review_required: bool | None = None
    lot_batch_review_required: bool | None = None
    inventory_inspection_required: bool | None = None
    trend_scan_required: bool | None = None
    customer_outreach_required: bool | None = None
    frontline_guidance_lookup_required: bool | None = None
    technical_services_response_required: bool | None = None


class ReviewSummary(StrictBaseModel):
    record_review_result: RecordReviewResult
    lot_batch_pattern_summary: LotBatchPatternSummary
    inventory_inspection_result: InventoryInspectionResult
    customer_context_summary: str | None = None
    api_reference_review_result: ApiReferenceReviewResult
    missing_information: list[str] = Field(default_factory=list)
    evidence_limitations: list[str] = Field(default_factory=list)
    severe_triggers_observed: list[EscalationTrigger] = Field(default_factory=list)


class DerivedAssessment(StrictBaseModel):
    reviewer_assigned_classification: FormalClassification
    reviewer_assigned_category: FormalCategory | None = None
    reviewer_assigned_subcategory: FormalSubcategory | None = None
    concern_type: ConcernType
    risk_lane: RiskLane
    review_scope: ReviewScope
    escalation_triggers: list[EscalationTrigger] = Field(default_factory=list)
    handling_path: HandlingPath
    resolution_review_required: bool
    resolution_options: list[ResolutionOption] = Field(default_factory=list)
    rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_category_rules(self) -> Self:
        if self.reviewer_assigned_classification == FormalClassification.QRE:
            if self.reviewer_assigned_category is None:
                raise ValueError("QRE assessments require reviewer_assigned_category")
            if self.reviewer_assigned_subcategory is None:
                raise ValueError("QRE assessments require reviewer_assigned_subcategory")

        if self.reviewer_assigned_classification == FormalClassification.GENERAL_QUESTION:
            if self.reviewer_assigned_category is not None:
                raise ValueError("general_question assessments should not have reviewer_assigned_category")
            if self.reviewer_assigned_subcategory is not None:
                raise ValueError("general_question assessments should not have reviewer_assigned_subcategory")

        return self

    @model_validator(mode="after")
    def validate_resolution_rules(self) -> Self:
        if not self.resolution_review_required and self.resolution_options:
            raise ValueError("resolution_options should be empty when resolution_review_required is false")
        return self


class ExpectedStructuredOutput(StrictBaseModel):
    raw_intake: RawIntake
    product_context: ProductContext
    investigation_requirements: InvestigationRequirements
    review_summary: ReviewSummary
    derived_assessment: DerivedAssessment


# Backward-compatible checklist classes. Runtime checklist code may also use app.checklist_models.
class EvidenceCitation(StrictBaseModel):
    chunk_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_title: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    section_heading: str = Field(min_length=1)
    score: float | None = None
    matched_terms: list[str] = Field(default_factory=list)
    supporting_text: str = Field(min_length=1)


class ChecklistItem(StrictBaseModel):
    check_name: str = Field(min_length=1)
    required: bool
    rationale: str = Field(min_length=1)
    evidence: list[EvidenceCitation] = Field(default_factory=list)


class IntakeChecklist(StrictBaseModel):
    concern_text: str = Field(min_length=1)
    likely_concern_type: ConcernType | None = None
    likely_risk_lane: RiskLane | None = None
    review_checks: list[ChecklistItem] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    escalation_triggers_to_rule_out: list[EscalationTrigger] = Field(default_factory=list)
    evidence: list[EvidenceCitation] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class RefusalReason(StrEnum):
    EXTERNAL_DRUG_REFERENCE = "external_drug_reference"
    INTERNAL_RECORD_ACCESS = "internal_record_access"
    CLINICAL_OR_LEGAL_CONCLUSION = "clinical_or_legal_conclusion"


class RefusalResult(StrictBaseModel):
    refused: bool
    reason: RefusalReason | None = None
    message: str | None = None
    matched_terms: list[str] = Field(default_factory=list)


class IntakeUnderstanding(StrictBaseModel):
    raw_intake: RawIntake
    product_context: ProductContext
    possible_boundary_issue: RefusalReason | None = None
    boundary_supporting_phrase: str | None = None
    extracted_customer_context: str | None = None
    facts_present: list[str] = Field(default_factory=list)
    facts_missing: list[str] = Field(default_factory=list)


class ExtractionEvidenceStatus(StrEnum):
    EXPLICIT = "explicit"
    NORMALIZED = "normalized"
    AMBIGUOUS = "ambiguous"
    NOT_STATED = "not_stated"


class ReviewSummaryFieldEvidence(StrictBaseModel):
    field_name: str = Field(min_length=1)
    status: ExtractionEvidenceStatus
    supporting_quote: str | None = None
    explanation: str | None = None


class UnresolvedReviewQuestion(StrictBaseModel):
    field_name: str = Field(min_length=1)
    question: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    decision_impact: list[str] = Field(default_factory=list)


class ReviewSummaryExtractionResult(StrictBaseModel):
    review_summary: ReviewSummary
    field_evidence: list[ReviewSummaryFieldEvidence] = Field(default_factory=list)
    unresolved_questions: list[UnresolvedReviewQuestion] = Field(default_factory=list)

