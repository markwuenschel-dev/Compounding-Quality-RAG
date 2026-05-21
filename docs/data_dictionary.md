# Compounding Quality RAG Data Dictionary

Version: 0.2  
Project: Compounding Quality Inquiry Evidence Assistant  
Data boundary: synthetic public learning artifact only

## 1. Purpose

This data dictionary defines controlled fields, allowed values, and metadata rules for the synthetic Compounding Quality RAG project. It supports two workflow modes:

| Mode | Input | Output |
|---|---|---|
| Intake/checklist mode | Raw concern narrative from a QRE/general-question form or customer review | Checklist of what should be checked, missing information, risk-lane clues, frontline-guidance possibilities, and cited SOP guidance. |
| Review-summary mode | Completed human-entered or synthetic review findings | Supported handling path, escalation/refusal notes, resolution options, and cited evidence. |

The project uses a carry-forward schema: a record can begin as `workflow_stage: intake_only`, then later be updated to `review_summary_complete` or `finalized` once a reviewer has completed investigation steps.

## 2. Core Design Rules

- The public project uses synthetic records only.
- The RAG system does not mutate source systems.
- The RAG system does not directly inspect physical inventory, compounding records, customer accounts, external drug references, or internal systems.
- The RAG system may suggest structured fields from narrative, but reviewer confirmation is required before those fields become authoritative.
- SOP-like documents can support process guidance.
- Synthetic inquiry records can support examples, pattern recognition, and test cases only.
- Synthetic inquiry examples must not override SOP guidance.
- If authoritative SOP evidence is missing, the system should refuse process guidance or state that the corpus does not support the answer.
- Severe escalation routing should use reviewer-confirmed structured fields, not raw free-text keyword matching.

## 3. Source Types and Authority Rules

| Field | Allowed values | Required | Notes |
|---|---|---|---|
| `source_type` | `sop`, `synthetic_inquiry`, `synthetic_api_reference`, `eval_question` | Yes | Used for authority separation and retrieval filtering. |
| `synthetic` | `true` | Yes | All public portfolio records must be synthetic. |

## 4. SOP Metadata Fields

SOP Markdown files should start with a consistent metadata block.

| Field | Type | Required | Example | Notes |
|---|---|---|---|---|
| `Document ID` | string | Yes | `SOP-001` | Stable source ID. |
| `Title` | string | Yes | `Intake Classification and Risk Lane Assignment` | Human-readable title. |
| `Version` | string | Yes | `1.0` | Synthetic document version. |
| `Effective Date` | string | Yes | `2026-05-04` | Synthetic effective date. |
| `Process Area` | string | Yes | `intake classification` | Used for filtering and review. |
| `Source Type` | string | Yes | `sop` | Must be `sop`. |
| `Synthetic` | boolean/string | Yes | `true` | Must indicate synthetic status. |

## 5. Synthetic Inquiry File Contract

Synthetic inquiry records should be stored as YAML files. The public project should use synthetic IDs, not real QRE numbers, customer-review tracker IDs, order IDs, customer identifiers, patient identifiers, or real compounding-record identifiers.

Example path:

```text
data/synthetic_inquiries/INQ-SYN-001.yaml
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `inquiry_id` | string | Yes | Synthetic record ID, e.g. `INQ-SYN-001`. |
| `schema_version` | string | Yes | Supports future schema changes. |
| `source_type` | string | Yes | Must be `synthetic_inquiry`. |
| `synthetic` | boolean | Yes | Must be `true`. |
| `workflow_stage` | enum | Yes | `intake_only`, `review_summary_complete`, or `finalized`. |
| `raw_intake` | object | Yes | What was available at intake. |
| `product_context` | object | Yes | Synthetic product/dosage metadata, often unknown at intake. |
| `review_summary` | object or null | Yes | Human-entered or synthetic review findings. Null at intake. |
| `derived_assessment` | object or null | Yes | Classification, risk lane, handling path, and rationale. Null at intake unless already reviewed. |

## 6. Workflow Stage Values

| Value | Meaning |
|---|---|
| `intake_only` | Raw intake has been captured, but reviewer investigation is not complete. `review_summary` and `derived_assessment` are usually null. |
| `review_summary_complete` | Reviewer findings have been entered, but the final derived assessment is not confirmed. |
| `finalized` | Reviewer findings and final assessment are complete. |

## 7. Raw Intake Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `intake_source` | enum | Yes | Actual ingestion channel. Allowed: `qre_general_question_form`, `customer_review`. |
| `submitter_role` | enum | Yes | Who submitted or triggered the record. Allowed values below. |
| `submission_purpose` | enum | Yes | Why the submission exists. Allowed values below. |
| `concern_narrative` | string | Yes | Raw or lightly de-identified intake narrative. Should sound like form/review text, not a polished assessment. |
| `star_rating` | integer or null | Yes | Always present for `customer_review`; null otherwise. |
| `review_text_present` | boolean or null | Yes | Required for `customer_review`; null otherwise. |
| `submitter_selected_classification` | enum or null | Optional | Submitter may select `qre` or `general_question`; reviewer may correct it. |

Do not include `submitter_selected_category` or `submitter_selected_subcategory`. Those are reviewer-assigned fields and should not exist at intake.

## 8. Intake Source Values

- `qre_general_question_form`
- `customer_review`

A frontline pharmacist question is not a separate intake source. It is modeled as the QRE/general-question form plus `submitter_role: frontline_pharmacist` and `submission_purpose: frontline_pharmacist_question`.

## 9. Submitter Role Values

- `frontline_pharmacist`
- `customer_care`
- `technical_services`
- `operations_leadership`
- `customer_review_system`
- `unknown`

## 10. Submission Purpose Values

- `customer_reported_concern`
- `frontline_pharmacist_question`
- `documentation_update`
- `escalation_request`
- `customer_review_followup`
- `other`

## 11. Review Scope Values

`review_scope` is a derived or reviewer-confirmed field that describes how much investigation is needed.

- `guidance_only`
- `customer_review_record_check`
- `full_quality_review`
- `escalation_review`
- `insufficient_information`

Frontline pharmacist questions usually map to `guidance_only` unless the narrative includes a product-quality concern, suspected ADE, dispensing error, or escalation trigger.

## 12. Product Context Fields

| Field | Allowed values or type | Notes |
|---|---|---|
| `species` | `cat`, `dog`, `horse`, `other`, `unknown` | Often unknown at intake unless stated in the narrative or retrieved from an approved source. |
| `dosage_form` | `oral_liquid`, `capsule`, `tablet`, `transdermal`, `chewable`, `powder`, `ophthalmic`, `oral_paste`, `other`, `unknown` | May be unknown at intake. |
| `product_placeholder` | string or null | Synthetic placeholder only. |
| `flavor_or_attribute` | string or null | May be unknown at intake even if flavor exists in downstream order data. |
| `bud_present` | boolean or null | If compounding-record metadata is modeled, BUD is assumed present. Null when not accessed. |
| `batch_lot_present` | boolean or null | If compounding-record metadata is modeled, batch/lot is assumed present. Null when not accessed. |

## 13. Investigation Requirements Fields

These fields should be generated or confirmed as checklist outputs, not assumed as raw intake facts.

| Field | Type | Notes |
|---|---|---|
| `record_review_required` | boolean | Whether a compounding-record review is required. |
| `lot_batch_review_required` | boolean | Whether a lot/batch pattern check is required. |
| `inventory_inspection_required` | boolean | Whether remaining inventory should be checked if available. |
| `trend_scan_required` | boolean | Whether trend/pattern review is appropriate. |
| `customer_outreach_required` | boolean | Whether customer outreach or clarification is needed. |
| `frontline_guidance_lookup_required` | boolean | Whether known frontline guidance should answer the question. |
| `technical_services_response_required` | boolean | Whether TS should respond to the submitter. |

For intake-only YAML records, these may be absent or null unless the file is being used as an expected-output fixture.

## 14. Review Summary Fields

| Field | Allowed values or type | Notes |
|---|---|---|
| `record_review_result` | `no_discrepancy_found`, `documentation_incomplete`, `documentation_discrepancy_found`, `not_applicable` | Reviewer-entered or synthetic review finding. |
| `lot_batch_pattern_summary` | `no_similar_batch_concerns_found`, `similar_concern_same_batch_found`, `similar_concern_same_medication_dosage_form_found`, `trend_threshold_met`, `unavailable`, `not_applicable` | Limited by available synthetic fields. |
| `inventory_inspection_result` | `no_inventory_available`, `no_visual_concern_found`, `visual_concern_found`, `not_checked`, `not_applicable` | Does not imply the RAG system inspected inventory. |
| `customer_context_summary` | string | Information provided in synthetic submission or outreach summary only. |
| `api_reference_review_result` | `not_needed`, `synthetic_reference_consulted`, `external_reference_needed`, `not_supported_by_public_corpus` | Public project cannot use licensed external drug-information content. |
| `severe_triggers_observed` | list of escalation-trigger enums | Structured reviewer-confirmed severe triggers observed during review. Empty list if none were observed. This field drives final escalation routing and prevents brittle free-text parsing of phrases like “no hospitalization.” |
| `missing_information` | list | Fields still needed. |
| `evidence_limitations` | list | Limits of the available evidence. |

## 15. Derived Assessment Fields

| Field | Type | Notes |
|---|---|---|
| `reviewer_assigned_classification` | `qre`, `general_question` | Reviewer-confirmed. |
| `reviewer_assigned_category` | enum or null | Required for QRE, null for general question. |
| `reviewer_assigned_subcategory` | enum or null | Required for QRE, null for general question. |
| `concern_type` | enum | Controlled concern type. |
| `risk_lane` | enum | Risk severity/workflow lane. |
| `review_scope` | enum | Investigation depth. |
| `escalation_triggers` | list of escalation-trigger enums | Derived from `review_summary.severe_triggers_observed`. Empty if none were confirmed. |
| `handling_path` | enum | What happens operationally. |
| `resolution_review_required` | boolean | Whether customer-facing resolution review is needed. |
| `resolution_options` | list | Empty if none. |
| `rationale` | string | Synthetic explanation. |

## 16. Formal Classification Values

- `qre`
- `general_question`

## 17. Formal QRE Categories and Subcategories

| Category | Subcategories |
|---|---|
| `customer_service_related` | `customer_experience`; `autoship_issue`; `click_to_delivery`; `packaging`; `pricing` |
| `equipment_device_related` | `missing_equipment`; `defective_device`; `syringe_issue` |
| `medication_related` | `flavor`; `bud`; `formulation`; `package_size`; `efficacy` |
| `suspected_ade` | `suspected_ade`; `flavor_related_ade` |
| `dispensing_error` | `wrong_quantity`; `wrong_patient`; `wrong_medication`; `wrong_directions`; `missing_item`; `compounding_error`; `data_supply_discrepancy`; `labeling_error` |

## 18. Concern Type Values

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

## 19. Risk Lane Values

- `expected_self_limiting`
- `unexpected_non_life_threatening`
- `life_threatening_or_legal`

## 20. Handling Path Values

- `document_only_no_action`
- `delegate_to_frontline_pharmacist`
- `respond_to_frontline_pharmacist`
- `technical_services_customer_outreach`
- `record_review_then_document`
- `investigate_to_resolution`
- `flag_leadership_during_investigation`
- `leadership_escalation_before_resolution`
- `insufficient_information`

`respond_to_frontline_pharmacist` is used when the frontline pharmacist is asking Technical Services a guidance question. `delegate_to_frontline_pharmacist` is used when a customer-reported concern should be handled using guidance already available to frontline pharmacists.

## 21. Resolution Option Values

- `replacement_or_reship_review`
- `refund_or_concession_review`
- `alternate_dosage_form_discussion`
- `counseling_or_follow_up`
- `leadership_directed_resolution`
- `no_customer_facing_resolution`

## 22. Escalation Trigger Values

- `pet_death`
- `pet_hospitalization`
- `threatened_legal_action`
- `veterinarian_alleges_harm_from_compound`
- `possible_contamination`
- `wrong_patient_or_wrong_medication`
- `repeat_issue_same_lot_or_batch_with_conditions`
- `rare_regulatory_or_compliance_concern`

## 23. Delegate-Back and Frontline Response Reasons

- `ingredient_presence_question`
- `oral_liquid_shortage_counseling`
- `temperature_excursion_professional_judgment`
- `routine_palatability_or_flavor_rejection`
- `limited_guidance_specialty_compound_question`

## 24. Customer Review Rules

Customer review records always include a star rating. Review text is optional. One- to three-star reviews with no text are record-reviewed and documented if no quality concern is found. One- to three-star reviews with text generally require record review and customer outreach. Four- and five-star reviews do not require routine follow-up unless text suggests a safety or quality concern.

## 25. Frontline Pharmacist Question Rules

Frontline pharmacist questions are submitted through the QRE/general-question form and should be represented with:

```yaml
intake_source: qre_general_question_form
submitter_role: frontline_pharmacist
submission_purpose: frontline_pharmacist_question
```

They usually remain `formal_classification: general_question` and usually require `review_scope: guidance_only`. They should not trigger compounding-record review, lot/batch review, inventory inspection, trend scanning, or customer outreach unless the narrative includes a product-quality concern, suspected ADE, dispensing error, or escalation trigger.

## 26. Specific Workflow Rules

- Oral liquid shortage usually delegates to frontline unless leakage, package damage, record discrepancy, or temperature excursion is present.
- Temperature excursion claims should not overstate product-specific safety.
- Ingredient presence questions may confirm or deny a specific ingredient but should not provide a full ingredient list.
- Routine palatability concerns are expected/self-limiting unless severe vomiting or global escalation triggers are present.
- External drug-information claims require synthetic reference support or refusal.

## 27. Citation Metadata Contract

Citations must identify:

- `source_id`
- `source_title`
- `source_type`
- `chunk_id`
- `section_heading` for SOPs

Debug output may include retrieval score and metadata.

## 28. Evaluation Data Notes

Evaluation questions should be separate from the retrieval corpus. They should cover checklist questions, review-summary conclusions, similar-case retrieval, escalation/refusal, source-type authority, and unsupported questions.

## 29. Public-Safety Boundary

The public project must not include real customer, patient, veterinarian, or order identifiers; PHI; PII; proprietary SOP language; internal screenshots or branding; real compounding records; real customer reviews; licensed drug-information content; or direct internal system names/APIs.
