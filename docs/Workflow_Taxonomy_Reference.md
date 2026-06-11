# Workflow Taxonomy Reference

Synthetic: true  
Source Type: reference

This reference summarizes controlled values and workflow contracts used by the synthetic SOP set, synthetic inquiry records, Python bridge, Spring API, and Phase 4 retrieval-evaluation layer.

## Core Model

- `intake_source`: where the record entered the system.
- `submitter_role`: who submitted the form or concern.
- `submission_purpose`: why the record was submitted.
- `formal_classification`: documentation bucket such as `qre` or `general_question`.
- `formal_category` / `formal_subcategory`: reviewer-assigned QRE category values.
- `concern_type`: what happened or what question is being asked.
- `review_scope`: how much review is needed.
- `risk_lane`: severity and escalation lane.
- `investigation_requirements`: checklist flags indicating which reviews should be performed.
- `review_summary`: reviewer-entered or synthetic findings.
- `handling_path`: what Technical Services does next.
- `resolution_options`: possible customer-facing closure options.
- `intake_understanding`: optional structured facts extracted from the initial concern.
- `evidence`: retrieved synthetic SOP chunks.
- `retrieval_strategy`: internal retrieval implementation being evaluated, such as keyword or local embedding.
- `retrieval_metrics`: evaluation outputs such as hit-rate@k, MRR, failed IDs, and latency.

## Workflow Stages

| Endpoint / artifact | Stage |
|---|---|
| `POST /api/checklist` | Phase 1 intake/checklist support. |
| `POST /api/retrieve` | Evidence lookup support. |
| `POST /api/final-assessment` | Phase 2 final assessment from structured reviewer findings. |
| CLI Phase 1 | Checklist. |
| CLI Phase 2 | Final review-support report. |
| `app.retrieval_evaluate` | Labeled retrieval-question evaluation. |
| `app.retrieval_compare` | Retriever comparison report generation. |

## Intake Sources

- `qre_general_question_form`
- `customer_review`

Do not use `frontline_pharmacist_question` as an intake source. Frontline pharmacist questions arrive through the QRE/general-question form.

## Submitter Roles

- `frontline_pharmacist`
- `customer`
- `customer_care`
- `customer_review_system`
- `technical_services`
- `operations_leadership`
- `other`
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

A submission is a QRE if it fits one of the formal QRE categories. Otherwise it is a general question. Technical Services may correct submitted classification during review.

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

## Boundary / Refusal Reasons

- `internal_record_access`: real order status, stock availability, inventory, customer history, compounding records, patient records, or internal-system access.
- `external_drug_reference`: Plumb's, package inserts, dose ranges, interactions, toxicity, or medication-specific safety claims.
- `clinical_or_legal_conclusion`: causality, diagnosis, safety determination, death causation, liability, legal advice, or final clinical/legal conclusion.

## Review Scopes

- `full_quality_review`
- `customer_review_record_check`
- `guidance_only`
- `escalation_review`
- `insufficient_information`

## Risk Lanes

- `expected_self_limiting`
- `unexpected_non_life_threatening`
- `life_threatening_or_legal`

Risk lane is derived from concern context and review findings. It is not usually a raw intake field.

## Investigation Requirements

- `record_review_required`
- `lot_batch_review_required`
- `inventory_inspection_required`
- `trend_scan_required`
- `customer_outreach_required`
- `frontline_guidance_lookup_required`
- `technical_services_response_required`

These flags describe what should be checked. They do not mean the RAG system directly inspected relevant operational systems.

## Review Summary Fields

- `record_review_result`
- `lot_batch_pattern_summary`
- `inventory_inspection_result`
- `customer_context_summary`
- `api_reference_review_result`
- `missing_information`
- `evidence_limitations`
- `severe_triggers_observed`

Review-summary fields are human-entered or synthetic findings. Public demo output must not claim real system access.

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

## Resolution Options

- `replacement_or_reship_review`
- `refund_or_concession_review`
- `alternate_dosage_form_discussion`
- `counseling_or_follow_up`
- `leadership_directed_resolution`
- `no_customer_facing_resolution`

## Escalation Triggers

- `pet_death`
- `pet_hospitalization`
- `threatened_legal_action`
- `veterinarian_alleges_harm_from_compound`
- `possible_contamination`
- `wrong_patient_or_wrong_medication`
- `repeat_issue_same_lot_or_batch_with_conditions`
- `rare_regulatory_or_compliance_concern`

Escalation-critical facts should be structured. Negated phrases such as “no hospitalization” should not create severe triggers.

## Retrieval Strategies

| Strategy | Contract role | Notes |
|---|---|---|
| `keyword` | Transparent baseline | Lexical matching with deterministic sorting and matched terms. |
| `embedding` | Local vector baseline | Hashing-vector cosine similarity used for plumbing and comparison, not production semantic search. |
| `hybrid` | Planned | Future strategy combining keyword and semantic signals. |

## Retrieval Metrics

| Metric | Meaning |
|---|---|
| `hit_rate_at_k` | Per-question binary hit averaged across questions. A question hits when at least one expected source appears in top-k. |
| `mean_reciprocal_rank` | Average reciprocal rank of the first expected source. |
| `failed_question_ids` | Retrieval questions where no expected source appeared in top-k. |
| `latency_seconds` | Wall-clock time for evaluating a retriever. |

Metric guardrails:

- `hit_rate_at_k` is not recall@k.
- Multiple expected sources do not create additive MRR credit.
- Raw `score` values are retriever-specific.
- The comparison report should measure retriever behavior, not assume which retriever wins.

## Python API Runner Bridge

Supported commands:

| Command | Purpose |
|---|---|
| `checklist` | Phase 1 checklist generation. |
| `retrieve` | Evidence retrieval. |
| `final_assessment` | Phase 2 final assessment. |

Response envelopes:

- `{"ok":true,"result":{...}}`
- `{"ok":false,"error":{...}}`

stdout is reserved for JSON. stderr is diagnostics.

## Spring API Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Service health. |
| `POST /api/checklist` | Checklist from concern text. |
| `POST /api/retrieve` | Evidence citations. |
| `POST /api/final-assessment` | Final assessment from concern text and structured review summary. |

## Spring API Error Contract

`ApiErrorResponse` fields:

- `timestamp`
- `status`
- `error`
- `message`
- `path`
- `requestId`
- `fieldErrors`
- `code` optional engine code

Mappings:

- Validation or malformed JSON -> 400.
- Python `INVALID_REQUEST` or `REFUSED` -> 422.
- Python timeout -> 504.
- Python interrupted -> 503.
- Process/stdout/response/mapping failures -> 502.
- Unexpected Java exception -> 500.

## Evidence Citation Fields

- `chunkId`
- `sourceId`
- `sourceTitle`
- `sourceType`
- `sectionHeading`
- `score`
- `matchedTerms`
- `supportingText`

## Public Demo Guardrails

The project must not claim to inspect or determine:

- real compounding records;
- inventory;
- order pages;
- customer history;
- patient records;
- Snowflake or internal databases;
- real proprietary SOPs;
- licensed drug references;
- clinical causality;
- legal liability;
- final customer-resolution decisions.

The correct behavior is synthetic review-support output or refusal.
