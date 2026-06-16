# Workflow Taxonomy Reference

Synthetic: true  
Source Type: reference

This reference summarizes the controlled values used by the synthetic SOP set and synthetic inquiry records. It is included to make review easier, not as an additional SOP.

## Core Model

- `intake_source`: where the record entered the system.
- `submitter_role`: who submitted the form or concern.
- `submission_purpose`: why the record was submitted.
- `formal_classification`: documentation bucket, such as `qre` or `general_question`.
- `formal_category` / `formal_subcategory`: reviewer-assigned QRE category values when the inquiry is a QRE.
- `concern_type`: what actually happened or what question is being asked.
- `review_scope`: how much review is needed.
- `risk_lane`: severity and escalation lane.
- `investigation_requirements`: checklist flags indicating which reviews should be performed.
- `review_summary`: reviewer-entered or synthetic summary of completed review findings.
- `handling_path`: what Technical Services does next.
- `resolution_options`: possible customer-facing closure or support options.

## Workflow Stages

- `intake_only`: raw intake has been captured, but review findings and derived assessment are not complete.
- `review_summary_complete`: reviewer findings have been entered, but the final derived assessment may not be complete.
- `finalized`: review summary and derived assessment are complete.

## Intake Sources

- `qre_general_question_form`
- `customer_review`

Do not use `frontline_pharmacist_question` as an intake source. Frontline pharmacist questions arrive through the QRE/general-question form.

## Submitter Roles

- `frontline_pharmacist`
- `customer`
- `customer_care`
- `technical_services`
- `operations_leadership`
- `unknown`

## Submission Purposes

- `customer_reported_concern`
- `frontline_pharmacist_question`
- `documentation_update`
- `escalation_request`
- `customer_review_followup`
- `other`

## Formal Classifications

- `qre`
- `general_question`

A submission is a QRE if it falls into one of the five formal QRE categories. If it does not fit one of those categories, it is a general question. Technical Services may correct the submitted classification during review.

## Formal QRE Categories and Subcategories

### `customer_service_related`

- `customer_experience`
- `autoship_issue`
- `click_to_delivery`
- `packaging`
- `pricing`

### `equipment_device_related`

- `missing_equipment`
- `defective_device`
- `syringe_issue`

### `medication_related`

- `flavor`
- `bud`
- `formulation`
- `package_size`
- `efficacy`

### `suspected_ade`

- `suspected_ade`
- `flavor_related_ade`

### `dispensing_error`

- `wrong_quantity`
- `wrong_patient`
- `wrong_medication`
- `wrong_directions`
- `missing_item`
- `compounding_error`
- `data_supply_discrepancy`
- `labeling_error`

## Concern Types

- `pet_refused_flavor`
- `smell_concern`
- `viscosity_or_thickness_concern`
- `color_change`
- `efficacy_concern`
- `possible_adverse_drug_event`
- `flavor_related_vomiting`
- `ingredient_presence_question`
- `oral_liquid_shortage`
- `temperature_excursion_question`
- `limited_guidance_specialty_compound_question`
- `syringe_or_device_issue`
- `package_damage_or_leakage`
- `broken_tablet_or_capsule_damage`
- `labeling_issue`
- `possible_dispensing_error`
- `wrong_patient_or_wrong_medication`
- `possible_contamination`
- `veterinarian_alleges_harm`
- `pet_hospitalized`
- `pet_death`
- `threatened_legal_action`

## Review Scopes

- `full_quality_review`
- `customer_review_record_check`
- `guidance_only`
- `escalation_review`
- `insufficient_information`

Frontline pharmacist questions generally use `guidance_only` unless the narrative alleges a product quality issue, suspected ADE, dispensing error, or escalation trigger.

## Risk Lanes

- `expected_self_limiting`
- `unexpected_non_life_threatening`
- `life_threatening_or_legal`

Risk lane is derived from the concern narrative, available facts, and review findings. It is not usually a raw intake field.

## Investigation Requirements

The investigation requirements object contains boolean checklist flags:

- `record_review_required`
- `lot_batch_review_required`
- `inventory_inspection_required`
- `trend_scan_required`
- `customer_outreach_required`
- `frontline_guidance_lookup_required`
- `technical_services_response_required`

These flags describe what should be checked. They do not mean the RAG system directly inspected the relevant operational systems.

## Review Summary Fields

- `record_review_result`
- `lot_batch_pattern_summary`
- `inventory_inspection_result`
- `customer_context_summary`
- `api_reference_review_result`
- `missing_information`
- `evidence_limitations`
- `severe_triggers_observed`

Review-summary fields are human-entered or synthetic review findings. The public project should not claim direct access to compounding records, inventory systems, lot-tracing systems, Snowflake, or external drug-information resources.

## Record Review Results

- `no_discrepancy_found`
- `documentation_incomplete`
- `documentation_discrepancy_found`
- `not_applicable`

## Lot / Batch Pattern Summary Values

- `no_similar_batch_concerns_found`
- `similar_concern_same_batch_found`
- `similar_concern_same_medication_dosage_form_found`
- `trend_threshold_met`
- `unavailable`
- `not_applicable`

## Inventory Inspection Results

- `no_inventory_available`
- `no_visual_concern_found`
- `visual_concern_found`
- `not_checked`
- `not_applicable`

## API Reference Review Results

- `not_needed`
- `synthetic_reference_consulted`
- `external_reference_consulted`
- `external_reference_needed`
- `not_supported_by_public_corpus`

Use `external_reference_consulted` when an outside source was already reviewed. Explicit supplier, manufacturer, or proprietary-formula non-disclosure maps to `not_supported_by_public_corpus`, even if outside information was reviewed.

## Review-Summary Defaulting Rule

When a review-summary field is not documented, the default depends on review scope.

### Guidance only

- record review: `not_applicable`
- lot/batch review: `not_applicable`
- inventory inspection: `not_applicable`
- reference review: `not_needed`

### Full quality or ADE investigation

- record review: `documentation_incomplete`
- lot/batch review: `unavailable`
- inventory inspection: `not_checked`
- reference review: `not_needed`

Explicit findings override defaults. For example, `One additional quality complaint was identified for the lot` maps to `similar_concern_same_batch_found`.

## Handling Paths

- `document_only_no_action`
- `delegate_to_frontline_pharmacist`
- `respond_to_frontline_pharmacist`
- `technical_services_customer_outreach`
- `record_review_then_document`
- `investigate_to_resolution`
- `flag_leadership_during_investigation`
- `leadership_escalation_before_resolution`
- `insufficient_information`

Use `respond_to_frontline_pharmacist` when Technical Services answers a frontline pharmacist question. Use `delegate_to_frontline_pharmacist` when Technical Services routes a routine customer-facing issue back to frontline handling.

## Resolution Options

- `replacement_or_reship_review`
- `refund_or_concession_review`
- `alternate_dosage_form_discussion`
- `counseling_or_follow_up`
- `leadership_directed_resolution`
- `no_customer_facing_resolution`

Resolution options are separate from handling path. They describe possible customer-facing closure options, not the primary review workflow.

## Escalation Triggers

- `pet_death`
- `pet_hospitalization`
- `threatened_legal_action`
- `veterinarian_alleges_harm_from_compound`
- `possible_contamination`
- `wrong_patient_or_wrong_medication`
- `repeat_issue_same_lot_or_batch_with_conditions`
- `rare_regulatory_or_compliance_concern`

Escalation triggers are structured findings in `review_summary.severe_triggers_observed`. A listed severe trigger reported in the complaint, such as hospitalization, may be proposed immediately for reviewer confirmation. Final routing should not rely on bare keyword matching in free text, because negated phrases such as “no hospitalization” or “no wrong medication concern” can otherwise be misread. Shortness of breath, collapse, and falling over remain clinical context unless another controlled severe trigger is present.

## Delegate-Back Reasons

- `ingredient_presence_question`
- `oral_liquid_shortage_counseling`
- `temperature_excursion_professional_judgment`
- `routine_palatability_or_flavor_rejection`
- `limited_guidance_specialty_compound_question`

## Customer Review Rules

Customer review records always include a star rating. Review text is optional.

- One- to three-star reviews with no text are record-reviewed and documented if no quality concern is found.
- One- to three-star reviews with text generally require record review and customer outreach.
- Four- and five-star reviews do not require routine follow-up unless text suggests a safety or quality concern.

## Frontline Pharmacist Question Rule

A frontline pharmacist question should be modeled as:

```yaml
intake_source: qre_general_question_form
submitter_role: frontline_pharmacist
submission_purpose: frontline_pharmacist_question
review_scope: guidance_only
```

This allows tracking frontline question volume without falsely modeling it as a separate ingestion source.

## Authority Rule

SOP-like documents can support process guidance. Synthetic inquiry records can support examples and pattern recognition only. Synthetic API-reference documents can support limited adverse-effect plausibility examples only. Evaluation questions are not authoritative evidence.

Synthetic inquiry examples must not override SOP guidance. If SOP evidence is missing, the system should refuse process guidance or state that the corpus does not support the answer.

## Public Boundary

All files are synthetic and generalized. Do not include internal screenshots, proprietary systems, real records, customer information, PHI, PII, licensed drug-reference content, internal system names, or exact internal SOP text in a public repository.
