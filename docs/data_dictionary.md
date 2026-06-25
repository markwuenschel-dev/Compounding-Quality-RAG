# Compounding Quality RAG Data Dictionary

Version: 0.4 — HTTP/API and retrieval-intent synced  
Updated: 2026-06-25  
Project: Compounding Quality Review Workbench  
Data boundary: synthetic public learning artifact only

## Purpose

This is the canonical public reference for controlled values, schema meaning, review-summary semantics, reference-review labels, severe-trigger handling, retrieval metadata, authority rules, and public safety boundaries.

Focused policy docs may explain a subset of these rules, but they should not contradict this file.

## Current runtime boundary

```text
React review-ui -> Spring Boot review-api -> Python FastAPI rag-engine
```

| Layer | Owns |
|---|---|
| React/TypeScript | Human-review workflow, typed API client consumption, loading/success/error state, reviewer interaction |
| Spring Boot | HTTP routes, DTO validation, OpenAPI, structured errors, readiness, request correlation, orchestration, HTTP client to Python |
| Python FastAPI | Refusal, retrieval, semantic intent detection, checklist generation, review-summary extraction, grounding, unresolved questions, final assessment, evaluation |

The public project does not claim direct access to real compounding records, order pages, inventory systems, customer history, internal SOPs, Snowflake, external drug references, or licensed clinical content.

## Schema boundaries

- Public data is synthetic only.
- SOP-like markdown documents are retrievable source truth.
- Synthetic inquiry examples are examples/test inputs, not authority over SOP-like guidance.
- Synthetic API-reference documents may support limited public-corpus examples only.
- Expected-output JSON files are hand-written/adjudicated gold labels.
- Evaluation questions are not source truth.
- Final severe escalation uses structured `review_summary.severe_triggers_observed`, not free-text keyword scanning.
- Current API workflow stages are operational: checklist generation, review-summary extraction/reviewer findings, final assessment.
- Older fixtures may contain `workflow_stage`; do not assume it is required in Spring API responses.

## Source types

| Value | Meaning |
|---|---|
| `sop` | Synthetic SOP-like source truth used for retrieval and process guidance |
| `synthetic_inquiry` | Synthetic example inquiry/case record |
| `synthetic_api_reference` | Synthetic reference-style public-corpus content |
| `eval_question` | Evaluation prompt/question; never authoritative evidence |

## Intake sources

- `qre_general_question_form`
- `customer_review`

Do not use `frontline_pharmacist_question` as an intake source. Use submitter role and submission purpose instead.

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

Formal classification is separate from `concern_type`, `risk_lane`, `review_scope`, `handling_path`, and `resolution_options`.

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

## Risk lanes

| Value | Meaning |
|---|---|
| `expected_self_limiting` | Expected/self-limiting concern when no severe trigger is confirmed |
| `unexpected_non_life_threatening` | Unexpected but non-life-threatening concern requiring review/follow-up |
| `life_threatening_or_legal` | Severe/legal lane driven by structured severe triggers |

## Review scopes

- `full_quality_review`
- `customer_review_record_check`
- `guidance_only`
- `escalation_review`
- `insufficient_information`

Frontline pharmacist questions generally use `guidance_only` unless the narrative alleges product-quality, ADE, dispensing-error, or severe-trigger facts.

## Investigation requirement flags

- `record_review_required`
- `lot_batch_review_required`
- `inventory_inspection_required`
- `trend_scan_required`
- `customer_outreach_required`
- `frontline_guidance_lookup_required`
- `technical_services_response_required`

These flags mean “should be checked.” They do not mean the public tool inspected real operational systems.

## Review summary values

### `record_review_result`

| Value | Meaning |
|---|---|
| `no_discrepancy_found` | Explicit record/worksheet review found no discrepancy |
| `documentation_incomplete` | Review is relevant/required but not documented or incomplete |
| `documentation_discrepancy_found` | Explicit discrepancy found |
| `not_applicable` | Review irrelevant to the guidance-only/narrow question |

### `lot_batch_pattern_summary`

| Value | Meaning |
|---|---|
| `no_similar_batch_concerns_found` | Explicit review found no similar concerns |
| `similar_concern_same_batch_found` | Similar concern found for same lot/batch |
| `similar_concern_same_medication_dosage_form_found` | Similar concern found at medication/dosage-form level |
| `trend_threshold_met` | Trend threshold met |
| `unavailable` | Relevant result unavailable/not documented |
| `not_applicable` | Lot/batch review irrelevant |

### `inventory_inspection_result`

| Value | Meaning |
|---|---|
| `no_inventory_available` | No retained inventory available |
| `no_visual_concern_found` | Inspection occurred; no visual concern |
| `visual_concern_found` | Inspection found a visual concern |
| `not_checked` | Inspection relevant but not documented |
| `not_applicable` | Inspection irrelevant |

### `api_reference_review_result`

| Value | Meaning |
|---|---|
| `not_needed` | No reference review mentioned or required |
| `synthetic_reference_consulted` | Public synthetic reference consulted |
| `external_reference_consulted` | Outside source reviewed and incorporated; source content not reproduced |
| `external_reference_needed` | Outside source still needs review |
| `not_supported_by_public_corpus` | Requested conclusion/disclosure cannot be supported publicly |

Reference precedence:

1. unsupported or non-disclosable;
2. completed external review;
3. completed synthetic-corpus review;
4. external review still needed;
5. no reference review needed.

## Review-summary defaulting

The extractor must not let the LLM decide what silence means.

| Missing field | Guidance-only default | Full-investigation default |
|---|---|---|
| record review | `not_applicable` | `documentation_incomplete` |
| lot/batch review | `not_applicable` | `unavailable` |
| inventory inspection | `not_applicable` | `not_checked` |
| reference review | `not_needed` | `not_needed` |

Explicit findings override defaults.

Related rules:

- Product concentration and package quantity do not establish administered dose.
- Numeric dose requires administration context such as `gave`, `administered`, `received`, `draws up`, or `per dose`.
- Device questions require actual failure context.
- Directions such as `2 clicks = 0.1 mL` do not imply device failure.
- Unresolved items must remain decision-relevant.

## Severe trigger policy

Structured values:

- `pet_death`
- `pet_hospitalization`
- `threatened_legal_action`
- `veterinarian_alleges_harm_from_compound`
- `possible_contamination`
- `wrong_patient_or_wrong_medication`
- `repeat_issue_same_lot_or_batch_with_conditions`
- `rare_regulatory_or_compliance_concern`

A listed severe trigger reported in the complaint may be proposed for reviewer confirmation. Final severe escalation should use `review_summary.severe_triggers_observed`.

Shortness of breath, collapse, falling over, neurologic signs, and similar clinical details remain context unless tied to an existing structured trigger.

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

Supplier/manufacturer/proprietary non-disclosure generally routes to `respond_to_frontline_pharmacist`.

## Resolution options

- `replacement_or_reship_review`
- `refund_or_concession_review`
- `alternate_dosage_form_discussion`
- `counseling_or_follow_up`
- `leadership_directed_resolution`
- `no_customer_facing_resolution`

Resolution options are separate from handling path.

## Species

- `cat`
- `dog`
- `horse`
- `other`
- `unknown`

## Dosage forms

- `oral_liquid`
- `capsule`
- `tablet`
- `transdermal`
- `chewable`
- `powder`
- `ophthalmic`
- `oral_paste`
- `topical`
- `other`
- `unknown`

## Citation metadata contract

Every citation should identify:

- `source_id`
- `source_title`
- `source_type`
- `chunk_id`
- `section_heading`
- `supporting_text`

Debug output may include retrieval score and matched terms.

## Retrieval intent metadata

Current accuracy-oriented retrieval path:

```text
concern text -> semantic intent detector -> deterministic workflow derivation -> vocabulary mapper -> keyword retriever
```

- Nano semantic intent detector: strongest measured frozen-holdout generalization path.
- Rule semantic intent detector: deterministic fallback.
- The model returns semantic facts only.
- Deterministic code derives workflow consequences.
- Rule fallback output must not be cached as Nano output.
- Raw query and deterministic expansion remain comparators.
- Embedding and hybrid retrievers are evaluation baselines only.

## Customer review rules

- Customer review records always include a star rating.
- Review text is optional.
- One- to three-star reviews with no text can be record-reviewed and documented if no quality/safety/ADE/defect/error/contamination/escalation facts exist.
- Low-star reviews with text generally require record review and customer outreach.
- Four- and five-star reviews do not require routine follow-up unless text suggests a safety or quality concern.

## Frontline pharmacist question rule

```yaml
intake_source: qre_general_question_form
submitter_role: frontline_pharmacist
submission_purpose: frontline_pharmacist_question
```

Usually `formal_classification: general_question` and `review_scope: guidance_only` unless quality/ADE/error/severe facts appear.

## Authority rules

- SOP-like documents support process guidance.
- Synthetic inquiry records support examples and pattern recognition only.
- Synthetic API-reference documents support limited adverse-effect plausibility examples only.
- Evaluation questions are not authoritative evidence.
- If SOP evidence is missing, the system should refuse or state that the corpus does not support the answer.

## Public safety boundary

Do not include:

- real customer, patient, veterinarian, order, prescription, compounding-record, inventory, or employee identifiers;
- PHI or PII;
- proprietary SOP language;
- internal screenshots or branding;
- licensed drug-information content;
- direct internal system names/APIs;
- claims that the tool accessed real records.

## Drift watchlist

Keep these synchronized:

- `data_dictionary.md`;
- `Workflow_Taxonomy_Reference.md`;
- `app/schemas.py`;
- Python models and TypeScript DTOs;
- expected-output JSON fixtures;
- focused policy docs;
- README/RUNBOOK/interview framing;
- failure-log prevention rules and regression tests.
