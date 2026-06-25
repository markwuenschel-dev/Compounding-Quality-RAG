# Workflow Taxonomy Reference

Synthetic: true  
Source Type: reference  
Updated: 2026-06-25

This reference summarizes controlled values used by the synthetic SOP set, synthetic inquiry records, expected outputs, and public UI/API workflow. It is not an SOP and should not override SOP-like source documents.

Use `data_dictionary.md` for full field contracts.

## Core model

| Concept | Meaning |
|---|---|
| `intake_source` | Where the record entered the workflow |
| `submitter_role` | Who submitted the form or concern |
| `submission_purpose` | Why the record was submitted |
| `formal_classification` | Documentation bucket such as `qre` or `general_question` |
| `formal_category` / `formal_subcategory` | Reviewer-assigned QRE category values |
| `concern_type` | What happened or what question is being asked |
| `review_scope` | How much review is needed |
| `risk_lane` | Severity and escalation lane |
| `investigation_requirements` | Checklist flags for what should be checked |
| `review_summary` | Reviewer-entered, extracted, or synthetic findings |
| `handling_path` | What Technical Services/reviewer does next |
| `resolution_options` | Possible customer-facing closure/support options |

## Workflow stages

Older fixtures may carry:

- `intake_only`
- `review_summary_complete`
- `finalized`

Current API workflow represents stages operationally through checklist generation, review-summary extraction/reviewer findings, and final assessment. Do not assume `workflow_stage` is required in current Spring API responses.

## Intake sources

- `qre_general_question_form`
- `customer_review`

Do not use `frontline_pharmacist_question` as an intake source.

## Submitter roles

- `frontline_pharmacist`
- `customer`
- `customer_care`
- `customer_review_system`
- `technical_services`
- `operations_leadership`
- `other`
- `unknown`

## Submission purposes

- `customer_reported_concern`
- `frontline_pharmacist_question`
- `documentation_update`
- `escalation_request`
- `customer_review_followup`
- `other`

## Formal classifications

- `qre`
- `general_question`

Formal classification is separate from concern type, risk lane, review scope, handling path, and resolution options.

## Formal QRE categories and subcategories

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
- `days_supply`

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
- `labeling_error`

## Concern types

- `pet_refused_flavor`
- `smell_concern`
- `viscosity_or_thickness_concern`
- `color_change`
- `efficacy_concern`
- `possible_adverse_drug_event`
- `flavor_related_vomiting`
- `ingredient_presence_question`
- `oral_liquid_shortage`
- `days_supply_question`
- `bud_question`
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

## Review scopes

- `full_quality_review`
- `customer_review_record_check`
- `guidance_only`
- `escalation_review`
- `insufficient_information`

Frontline pharmacist questions generally use `guidance_only` unless product-quality, ADE, dispensing-error, or escalation facts are present.

## Risk lanes

- `expected_self_limiting`
- `unexpected_non_life_threatening`
- `life_threatening_or_legal`

## Investigation requirements

- `record_review_required`
- `lot_batch_review_required`
- `inventory_inspection_required`
- `trend_scan_required`
- `customer_outreach_required`
- `frontline_guidance_lookup_required`
- `technical_services_response_required`

These flags do not mean the public system inspected operational systems.

## Review summary fields

- `record_review_result`
- `lot_batch_pattern_summary`
- `inventory_inspection_result`
- `customer_context_summary`
- `api_reference_review_result`
- `missing_information`
- `evidence_limitations`
- `severe_triggers_observed`

## Record review results

- `no_discrepancy_found`
- `documentation_incomplete`
- `documentation_discrepancy_found`
- `not_applicable`

## Lot/batch pattern summary values

- `no_similar_batch_concerns_found`
- `similar_concern_same_batch_found`
- `similar_concern_same_medication_dosage_form_found`
- `trend_threshold_met`
- `unavailable`
- `not_applicable`

## Inventory inspection results

- `no_inventory_available`
- `no_visual_concern_found`
- `visual_concern_found`
- `not_checked`
- `not_applicable`

## API reference review results

- `not_needed`
- `synthetic_reference_consulted`
- `external_reference_consulted`
- `external_reference_needed`
- `not_supported_by_public_corpus`

Explicit supplier/manufacturer/proprietary non-disclosure maps to `not_supported_by_public_corpus`, even if outside information was reviewed.

## Review-summary defaults

Guidance only:

- record review: `not_applicable`
- lot/batch: `not_applicable`
- inventory: `not_applicable`
- reference: `not_needed`

Full quality/ADE/error/device/shortage/efficacy investigation:

- record review: `documentation_incomplete`
- lot/batch: `unavailable`
- inventory: `not_checked`
- reference: `not_needed`

## Handling paths

- `document_only_no_action`
- `delegate_to_frontline_pharmacist`
- `respond_to_frontline_pharmacist`
- `technical_services_customer_outreach`
- `record_review_then_document`
- `investigate_to_resolution`
- `flag_leadership_during_investigation`
- `leadership_escalation_before_resolution`
- `insufficient_information`

Use `respond_to_frontline_pharmacist` for supplier/manufacturer/proprietary disclosure boundaries.

## Resolution options

- `replacement_or_reship_review`
- `refund_or_concession_review`
- `alternate_dosage_form_discussion`
- `counseling_or_follow_up`
- `leadership_directed_resolution`
- `no_customer_facing_resolution`

## Escalation triggers

- `pet_death`
- `pet_hospitalization`
- `threatened_legal_action`
- `veterinarian_alleges_harm_from_compound`
- `possible_contamination`
- `wrong_patient_or_wrong_medication`
- `repeat_issue_same_lot_or_batch_with_conditions`
- `rare_regulatory_or_compliance_concern`

Final routing should use structured `review_summary.severe_triggers_observed`, not free-text keyword scanning. Shortness of breath, collapse, falling over, neurologic signs, and similar context-only symptoms do not independently force severe escalation.

## Customer review rules

- One- to three-star reviews with no text are record-reviewed and documented if no quality/safety/ADE/defect/error/contamination/escalation facts are present.
- One- to three-star reviews with text generally require record review and customer outreach.
- Four- and five-star reviews do not require routine follow-up unless text suggests safety or quality concern.

## Frontline pharmacist question rule

```yaml
intake_source: qre_general_question_form
submitter_role: frontline_pharmacist
submission_purpose: frontline_pharmacist_question
review_scope: guidance_only
```

## Authority rule

SOP-like documents support process guidance. Synthetic inquiry records support examples only. Evaluation questions are not authoritative evidence. If SOP evidence is missing, the system should refuse or state that the corpus does not support the answer.

## Public boundary

All files are synthetic and generalized. Do not include internal screenshots, proprietary systems, real records, PHI, PII, licensed drug-reference content, internal system names, exact internal SOP text, or claims of real operational access.
