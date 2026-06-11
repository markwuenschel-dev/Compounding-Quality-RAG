# Compounding Quality RAG Data Dictionary


Version: 0.3 — v8 schema-synced  
Project: Compounding Quality Inquiry Evidence Assistant  
Data boundary: synthetic public learning artifact only


## 1. Purpose

This data dictionary is synchronized with `app/schemas.py` v8. It defines controlled values, model contracts, authority rules, and evidence metadata for the two-phase synthetic Compounding Quality RAG workflow.


## 2. Current Schema Boundaries

- The public project uses synthetic records only.
- SOP-like markdown documents are retrievable source truth.
- Expected-output JSON files are hand-written gold labels, not generated answers.
- Synthetic inquiry examples are inputs/test cases and must not override SOP guidance.
- Final escalation routing uses reviewer-confirmed `review_summary.severe_triggers_observed`, not raw free-text keyword matching.
- The current `ExpectedStructuredOutput` does not use `workflow_stage`; workflow stage is represented operationally by Phase 1 checklist output and Phase 2 reviewer findings.


## 3. Source Types

| Value | Notes |
|---|---|
| `sop` |  |
| `synthetic_inquiry` |  |
| `synthetic_api_reference` |  |
| `eval_question` |  |


## 4. Intake Sources

| Value | Notes |
|---|---|
| `qre_general_question_form` | QRE/general-question form, including frontline pharmacist questions. |
| `customer_review` | Moderated customer review workflow. |


## 5. Submitter Roles

| Value | Notes |
|---|---|
| `frontline_pharmacist` |  |
| `customer` |  |
| `customer_care` |  |
| `customer_review_system` |  |
| `technical_services` |  |
| `operations_leadership` |  |
| `other` |  |
| `unknown` |  |


## 6. Submission Purposes

| Value | Notes |
|---|---|
| `customer_reported_concern` |  |
| `frontline_pharmacist_question` |  |
| `documentation_update` |  |
| `escalation_request` |  |
| `customer_review_followup` |  |
| `other` |  |


## 7. Formal Classification Values

| Value | Notes |
|---|---|
| `qre` |  |
| `general_question` |  |


## 8. Formal QRE Categories

| Value | Notes |
|---|---|
| `customer_service_related` |  |
| `equipment_device_related` |  |
| `medication_related` |  |
| `suspected_ade` |  |
| `dispensing_error` |  |


## 9. Formal QRE Subcategories

| Value | Notes |
|---|---|
| `customer_experience` |  |
| `autoship_issue` |  |
| `click_to_delivery` |  |
| `packaging` |  |
| `pricing` |  |
| `missing_equipment` |  |
| `defective_device` |  |
| `syringe_issue` |  |
| `flavor` |  |
| `bud` |  |
| `formulation` |  |
| `package_size` |  |
| `efficacy` |  |
| `days_supply` |  |
| `suspected_ade` |  |
| `flavor_related_ade` |  |
| `wrong_quantity` |  |
| `wrong_patient` |  |
| `wrong_medication` |  |
| `wrong_directions` |  |
| `missing_item` |  |
| `compounding_error` |  |
| `labeling_error` |  |


## 10. Concern Types

| Value | Notes |
|---|---|
| `pet_refused_flavor` |  |
| `smell_concern` |  |
| `viscosity_or_thickness_concern` |  |
| `color_change` |  |
| `efficacy_concern` |  |
| `possible_adverse_drug_event` |  |
| `flavor_related_vomiting` |  |
| `ingredient_presence_question` |  |
| `oral_liquid_shortage` |  |
| `days_supply_question` |  |
| `bud_question` |  |
| `temperature_excursion_question` |  |
| `limited_guidance_specialty_compound_question` |  |
| `syringe_or_device_issue` |  |
| `package_damage_or_leakage` |  |
| `broken_tablet_or_capsule_damage` |  |
| `labeling_issue` |  |
| `possible_dispensing_error` |  |
| `wrong_patient_or_wrong_medication` |  |
| `possible_contamination` |  |
| `veterinarian_alleges_harm` |  |
| `pet_hospitalized` |  |
| `pet_death` |  |
| `threatened_legal_action` |  |


## 11. Risk Lanes

| Value | Notes |
|---|---|
| `expected_self_limiting` | Expected/self-limiting concern when no severe trigger is confirmed. |
| `unexpected_non_life_threatening` | Unexpected concern such as non-severe vomiting/ADE context requiring review and follow-up. |
| `life_threatening_or_legal` | Severe or high-risk lane driven by structured severe triggers such as hospitalization, death, legal threat, contamination, or wrong patient/medication. |


## 12. Review Scope Values

| Value | Notes |
|---|---|
| `full_quality_review` |  |
| `customer_review_record_check` |  |
| `guidance_only` |  |
| `escalation_review` |  |
| `insufficient_information` |  |


## 13. Review Summary Controlled Values

### RecordReviewResult

| Value | Notes |
|---|---|
| `no_discrepancy_found` |  |
| `documentation_incomplete` |  |
| `documentation_discrepancy_found` |  |
| `not_applicable` |  |

### LotBatchPatternSummary

| Value | Notes |
|---|---|
| `no_similar_batch_concerns_found` |  |
| `similar_concern_same_batch_found` |  |
| `similar_concern_same_medication_dosage_form_found` |  |
| `trend_threshold_met` |  |
| `unavailable` |  |
| `not_applicable` |  |

### InventoryInspectionResult

| Value | Notes |
|---|---|
| `no_inventory_available` |  |
| `no_visual_concern_found` |  |
| `visual_concern_found` |  |
| `not_checked` |  |
| `not_applicable` |  |

### ApiReferenceReviewResult

| Value | Notes |
|---|---|
| `not_needed` |  |
| `synthetic_reference_consulted` |  |
| `external_reference_needed` |  |
| `not_supported_by_public_corpus` |  |


## 14. Handling Paths

| Value | Notes |
|---|---|
| `document_only_no_action` |  |
| `delegate_to_frontline_pharmacist` |  |
| `respond_to_frontline_pharmacist` |  |
| `technical_services_customer_outreach` |  |
| `record_review_then_document` |  |
| `investigate_to_resolution` |  |
| `flag_leadership_during_investigation` |  |
| `leadership_escalation_before_resolution` |  |
| `insufficient_information` |  |


## 15. Resolution Options

| Value | Notes |
|---|---|
| `replacement_or_reship_review` |  |
| `refund_or_concession_review` |  |
| `alternate_dosage_form_discussion` |  |
| `counseling_or_follow_up` |  |
| `leadership_directed_resolution` |  |
| `no_customer_facing_resolution` |  |


## 16. Escalation Triggers

| Value | Notes |
|---|---|
| `pet_death` |  |
| `pet_hospitalization` |  |
| `threatened_legal_action` |  |
| `veterinarian_alleges_harm_from_compound` |  |
| `possible_contamination` |  |
| `wrong_patient_or_wrong_medication` |  |
| `repeat_issue_same_lot_or_batch_with_conditions` |  |
| `rare_regulatory_or_compliance_concern` |  |


## 17. Species and Dosage Form Values

### Species

| Value | Notes |
|---|---|
| `cat` |  |
| `dog` |  |
| `horse` |  |
| `other` |  |
| `unknown` |  |

### DosageForm

| Value | Notes |
|---|---|
| `oral_liquid` |  |
| `capsule` |  |
| `tablet` |  |
| `transdermal` |  |
| `chewable` |  |
| `powder` |  |
| `ophthalmic` |  |
| `oral_paste` |  |
| `topical` |  |
| `other` |  |
| `unknown` |  |


## 18. Model Contracts

### `SopDocument`

| Field | Type | Required | Notes |
|---|---|---|---|
| `document_id` | string | Yes | Stable source ID such as `SOP-001`. |
| `title` | string | Yes | Human-readable synthetic SOP title. |
| `version` | string | Yes | Synthetic version. |
| `effective_date` | string | Yes | Synthetic effective date. |
| `process_area` | string | Yes | Filtering and review context. |
| `source_type` | literal `sop` | Yes | Must be SOP. |
| `synthetic` | literal `true` | Yes | Must be true in public corpus. |
| `body_text` | string | Yes | Markdown body after frontmatter. |

### `RawIntake`

| Field | Type | Required | Notes |
|---|---|---|---|
| `intake_source` | `IntakeSource` | Yes | Channel. |
| `submitter_role` | `SubmitterRole` | Yes | Who triggered or submitted the record. |
| `submission_purpose` | `SubmissionPurpose` | Yes | Why the record exists. |
| `concern_narrative` | string | Yes | Raw or lightly de-identified synthetic narrative. |
| `star_rating` | integer 1-5 or null | Conditional | Required for `customer_review`; forbidden for non-review intake. |
| `review_text_present` | boolean or null | Conditional | Required for `customer_review`; forbidden for non-review intake. |
| `submitter_selected_classification` | classification or null | Optional | Submitter selection, not final reviewer assignment. |

### `ProductContext`

| Field | Type | Notes |
|---|---|---|
| `species` | `Species` | Defaults to `unknown`. |
| `dosage_form` | `DosageForm` | Defaults to `unknown`. |
| `product_placeholder` | string or null | Synthetic placeholder only. |
| `flavor_or_attribute` | string or null | Flavor or product attribute when known. |
| `bud_present` | boolean or null | Null when not accessed/known. |
| `batch_lot_present` | boolean or null | Null when not accessed/known. |

### `InvestigationRequirements`

All fields are boolean or null: `record_review_required`, `lot_batch_review_required`, `inventory_inspection_required`, `trend_scan_required`, `customer_outreach_required`, `frontline_guidance_lookup_required`, and `technical_services_response_required`.

### `ReviewSummary`

| Field | Type | Notes |
|---|---|---|
| `record_review_result` | `RecordReviewResult` | Reviewer-entered or synthetic review finding. |
| `lot_batch_pattern_summary` | `LotBatchPatternSummary` | Lot/batch pattern finding or availability. |
| `inventory_inspection_result` | `InventoryInspectionResult` | Does not imply the tool inspected inventory. |
| `customer_context_summary` | string or null | Reviewer-entered/synthetic context. |
| `api_reference_review_result` | `ApiReferenceReviewResult` | Public repo cannot use licensed external drug info. |
| `missing_information` | list of strings | Remaining facts needed. |
| `evidence_limitations` | list of strings | Known evidence limitations. |
| `severe_triggers_observed` | list of `EscalationTrigger` | Structured source of truth for final severe escalation routing. |

### `DerivedAssessment`

| Field | Type | Notes |
|---|---|---|
| `reviewer_assigned_classification` | `FormalClassification` | QRE or general question. |
| `reviewer_assigned_category` | `FormalCategory` or null | Required for QRE; null for general question. |
| `reviewer_assigned_subcategory` | `FormalSubcategory` or null | Required for QRE; null for general question. |
| `concern_type` | `ConcernType` | Workflow/semantic concern type. |
| `risk_lane` | `RiskLane` | Risk/severity lane. |
| `review_scope` | `ReviewScope` | Review depth. |
| `escalation_triggers` | list of `EscalationTrigger` | Derived from structured severe triggers. |
| `handling_path` | `HandlingPath` | Operational next step. |
| `resolution_review_required` | boolean | Whether customer-facing resolution review is required. |
| `resolution_options` | list of `ResolutionOption` | Must be empty when `resolution_review_required` is false. |
| `rationale` | string | Synthetic explanation. |

### `ExpectedStructuredOutput`

Wrapper with `raw_intake`, `product_context`, `investigation_requirements`, `review_summary`, and `derived_assessment`.



## Retrieval Strategy Contracts

### Retriever Contract

All retrievers expose the same search contract:

```python
search(query: str, *, top_k: int = 5, source_type: str | None = None) -> list[SearchResult]
```

All retrievers return the same `SearchResult` shape:

| Field | Meaning |
|---|---|
| `chunk` | Retrieved chunk metadata and text. |
| `score` | Retriever-specific score used for ranking within that retriever. |
| `matched_terms` | Lexical terms that overlap between query and chunk when available. |

### Retrieval Strategies

| Strategy | Purpose | Current meaning |
|---|---|---|
| `keyword` | Transparent lexical baseline. | Stable baseline for exact SOP/process-term matching. |
| `embedding` | Local deterministic hashing-vector baseline. | Vector plumbing only; not production semantic search. |
| `hybrid` | Weighted combination of normalized keyword and vector scores. | Local comparison baseline. |

### Retrieval Metrics

| Metric | Meaning |
|---|---|
| `hit_rate_at_k` | Fraction of questions where at least one expected source appears in top-k. |
| `mean_reciprocal_rank` | Average reciprocal rank of the first expected source retrieved. |
| `failed_question_ids` | Retrieval question IDs where no expected source appeared in top-k. |
| `latency_seconds` | Wall-clock evaluation time for a retriever. |

### Metric Invariants

- Hit-rate is binary per question; it is not recall.
- MRR uses the first expected source found in retrieved order.
- Multiple expected sources are acceptable alternatives, not additive credit.
- Raw scores should not be compared directly across retriever types.
- Hybrid scores normalize keyword and vector components before weighting.

## 19. Citation Metadata Contract

Every citation should identify:

- `source_id`
- `source_title`
- `source_type`
- `chunk_id`
- `section_heading`
- `supporting_text`

Debug output may include retrieval score and matched terms. Source ID, section heading, and chunk ID are the minimum useful citation triad for reviewing why a claim was supported.

## 20. Customer Review Rules

Customer review records always include a star rating. Review text is optional. One- to three-star reviews with no text can be record-reviewed and documented if no quality concern, safety concern, suspected ADE, product defect, dispensing error, contamination, or escalation trigger is found. Low-star reviews with text generally require record review and customer outreach. Four- and five-star reviews do not require routine follow-up unless text suggests a safety or quality concern.

## 21. Frontline Pharmacist Question Rules

Frontline pharmacist questions use:

```yaml
intake_source: qre_general_question_form
submitter_role: frontline_pharmacist
submission_purpose: frontline_pharmacist_question
```

They usually remain `formal_classification: general_question` and `review_scope: guidance_only` unless the narrative includes a product-quality concern, suspected ADE, dispensing error, or structured severe trigger.

## 22. Specific Workflow Rules

- Routine palatability concerns are expected/self-limiting unless severe vomiting or global escalation triggers are confirmed.
- Vomiting after administration is treated conservatively as suspected ADE review-support context unless structured findings prove otherwise.
- BUD questions usually route to frontline/Technical Services guidance unless they include a product-quality concern or escalation trigger.
- Device issues support review and possible replacement/reship review when administration is affected.
- Wrong patient or wrong medication is handled conservatively as escalation before routine resolution.
- External drug-information claims require synthetic reference support or refusal.

## 23. Public-Safety Boundary

The public project must not include real customer, patient, veterinarian, order, prescription, compounding-record, inventory, or employee identifiers; PHI; PII; proprietary SOP language; internal screenshots or branding; licensed drug-information content; direct internal system names/APIs; or claims that the tool accessed real records.

## 24. Schema Drift Watchlist

Keep these in sync whenever either file changes:

- `data_dictionary.md` enum tables and `app/schemas.py` enum classes.
- `EvidenceCitation` fields in `app/checklist_models.py` and any backward-compatible copy in `app/schemas.py`.
- Expected-output JSON keys and `ExpectedStructuredOutput` fields.
- Retrieval citation metadata and README citation language.
- Failure log prevention rules and actual tests.
