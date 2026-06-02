# Compounding Quality RAG Data Dictionary


Version: 0.6 — Spring API error contract update  
Project: Compounding Quality Inquiry Evidence Assistant  
Data boundary: demo-only public learning artifact


## 1. Purpose

This data dictionary is synchronized with `app/schemas.py` v8. It defines controlled values, model contracts, authority rules, and evidence metadata for the two-phase synthetic Compounding Quality RAG workflow.


## 2. Current Schema Boundaries

- The public project uses synthetic records only.
- SOP-like markdown documents are retrievable source truth.
- Expected-output JSON files are hand-written gold labels, not generated answers.
- Synthetic inquiry examples are inputs/test cases and must not override SOP guidance.
- Final escalation routing uses reviewer-confirmed `review_summary.severe_triggers_observed`, not raw free-text keyword matching.
- Phase 1 can use `IntakeUnderstanding` to structure facts already present in the concern before checklist generation.
- `RefusalReason` and `RefusalResult` are schema-level contracts; `app/refusal.py` owns the detection logic.
- `app/api_runner.py` is a process bridge for Java/Spring integration. It accepts one JSON request from stdin and returns one JSON response on stdout.
- Bridge stdout must remain valid JSON only; diagnostics and tracebacks belong on stderr.
- The Spring Boot API exposes a centralized `ApiErrorResponse` contract for validation errors, malformed JSON, explicit response-status errors, and generic fallback errors.
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


## 17A. Boundary / Refusal Reason Values

| Value | Notes |
|---|---|
| `internal_record_access` | The request asks for real order status, inventory, customer history, compounding records, patient records, order pages, or internal-system data not available in the public demo. |
| `external_drug_reference` | The request asks for medication-specific claims requiring Plumb's, package inserts, drug handbooks, dose ranges, contraindications, interactions, toxicity, or published adverse-effect references. |
| `clinical_or_legal_conclusion` | The request asks the system to determine causality, safety, diagnosis, liability, death causation, legal advice, or another final clinical/legal conclusion. |

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

### `RefusalResult`

| Field | Type | Notes |
|---|---|---|
| `refused` | boolean | Whether the request should stop before checklist/final assessment. |
| `reason` | `RefusalReason` or null | Structured boundary reason when refused. |
| `message` | string or null | User-facing refusal message. |
| `matched_terms` | list of strings | Deterministic terms that matched, when applicable. |

### `IntakeUnderstanding`

| Field | Type | Notes |
|---|---|---|
| `raw_intake` | `RawIntake` | Original intake facts with `concern_narrative` copied verbatim. |
| `product_context` | `ProductContext` | Species, dosage form, flavor/attribute, BUD presence, and batch/lot presence stated in the concern. |
| `possible_boundary_issue` | `RefusalReason` or null | Semantic boundary issue extracted from the concern. This is not final refusal by itself until application logic handles it. |
| `boundary_supporting_phrase` | string or null | Shortest supporting phrase from the concern when a boundary issue is present. |
| `extracted_customer_context` | string or null | Neutral factual summary of customer-provided context, without clinical/legal conclusions. |
| `facts_present` | list of strings | Atomic facts explicitly stated in the concern. Used to avoid asking for facts already supplied. |
| `facts_missing` | list of strings | Relevant missing facts for review support; should not be a generic exhaustive checklist. |

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


### `ApiRunnerRequest`

The Python process bridge reads exactly one JSON object from stdin.

| Field | Type | Required | Notes |
|---|---|---|---|
| `command` | string | Yes | Currently supports `checklist`. |
| `payload` | object | Yes | Command-specific payload. |

Checklist payload:

| Field | Type | Required | Notes |
|---|---|---|---|
| `concernText` | string | Yes | Concern narrative passed from the Java API boundary. Must not be blank. |
| `topK` | integer | No | Optional retrieval count. Defaults to 5. Must be at least 1. |

### `ApiRunnerSuccessResponse`

| Field | Type | Notes |
|---|---|---|
| `ok` | literal `true` | Indicates the bridge handled the command and returned a usable result. |
| `result` | object | API-facing checklist result with camelCase keys for Java/Spring consumption. |

### `ApiRunnerErrorResponse`

| Field | Type | Notes |
|---|---|---|
| `ok` | literal `false` | Indicates the bridge handled the request but did not return a usable result, or returned a safe error envelope for an unexpected failure. |
| `error.code` | string | Stable machine-readable error code such as `INVALID_JSON`, `INVALID_REQUEST`, `UNKNOWN_COMMAND`, `REFUSED`, or `ENGINE_FAILURE`. |
| `error.message` | string | Human-readable error message suitable for Java-side translation. |
| `error.details` | object | Optional structured detail map, used for refusal reason and matched terms when available. |

Bridge exit-code rule:

| Case | Exit code | stdout |
|---|---:|---|
| Success | `0` | `{"ok":true,"result":{...}}` |
| Handled request/refusal error | `0` | `{"ok":false,"error":{...}}` |
| Unexpected bridge/engine failure | nonzero | `{"ok":false,"error":{"code":"ENGINE_FAILURE",...}}` |

### `ApiErrorResponse`

The Spring Boot API returns this centralized JSON error shape for handled API failures.

| Field | Type | Notes |
|---|---|---|
| `timestamp` | ISO-8601 string | Time the API error response was built. |
| `status` | integer | HTTP status code such as `400`, `404`, or `500`. |
| `error` | string | HTTP reason phrase such as `Bad Request` or `Internal Server Error`. |
| `message` | string | Stable user-facing message. Generic fallback errors must not leak implementation details. |
| `path` | string | Request path, such as `/api/checklist` or `/test/validate`. |
| `requestId` | string | Incoming `X-Request-Id` when present, otherwise a generated identifier. |
| `fieldErrors` | list | Validation errors. Empty for non-validation failures. |

`fieldErrors` entries use this shape:

| Field | Type | Notes |
|---|---|---|
| `field` | string | Field name that failed validation. |
| `rejectedValue` | any or null | Rejected value when safe to return. |
| `message` | string | Validation message. |

Spring API error mapping:

| Failure case | Expected status | Message rule |
|---|---:|---|
| Request-body validation failure | `400` | `Validation failed` with field errors. |
| Handler-method validation failure | `400` | `Validation failed`; field errors may be empty until mapped. |
| Malformed JSON body | `400` | Stable bad-request message with the centralized error shape. |
| `ResponseStatusException` | Exception status | Preserve status and provide non-empty message. |
| Unexpected exception | `500` | Generic message only; do not expose internal exception text. |


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
- `app/api_runner.py` bridge envelope and `tests/test_api_runner.py`.
- Spring `ApiErrorResponse`, `GlobalExceptionHandler`, and `GlobalExceptionHandlerTest` expected error shapes.
- Failure log prevention rules and actual tests.
