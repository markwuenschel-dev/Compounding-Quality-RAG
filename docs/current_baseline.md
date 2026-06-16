# Current Baseline

## Runtime architecture

- React/TypeScript provides the human-review workflow.
- Spring Boot owns HTTP routes, DTO validation, orchestration, readiness, error translation, OpenAPI, and the Python process boundary.
- Python owns intake structuring, refusal, retrieval, checklist generation, review-summary extraction, deterministic grounding, unresolved-question generation, final assessment, and evaluation.
- `GET /ready` checks Spring availability, the configured Python command, the Python working directory, and corpus availability.
- The React workflow displays backend readiness, disables submission while unavailable, distinguishes timeout/network/validation/engine/refusal errors, and supports retry.

## Review-summary extraction

The extraction pipeline is now a hybrid system:

1. The LLM converts the reviewer note into a candidate `ReviewSummary`.
2. Pydantic validates the controlled schema.
3. Deterministic grounding corrects explicit facts such as negation, completed reference review, non-disclosure boundaries, severe triggers, missing-information phrases, record review, lot patterns, and inventory findings.
4. A review-scope policy decides whether undocumented checks mean `not_applicable` or incomplete/not checked.
5. Decision-relevant unresolved questions are generated separately.
6. Evaluation compares controlled scalar fields and set-valued outputs against adjudicated cases.

### Development extraction benchmark

- Cases: `20`
- Scalar-field accuracy: `1.0`
- Missing-information precision: `1.0`
- Missing-information recall: `1.0`
- Severe-trigger precision: `1.0`
- Severe-trigger recall: `1.0`
- Unresolved-question precision: `1.0`
- Unresolved-question recall: `1.0`
- Failed case IDs: none

This is a development-set result, not proof of generalization. The holdout remains separate and should not be used for tuning.

## Reference-review policy

- `not_needed`: no reference review was mentioned or required.
- `synthetic_reference_consulted`: a reference contained in the public project corpus was used.
- `external_reference_consulted`: USP, manufacturer information, internal clinical guidance, a veterinary drug reference, or a package insert was already reviewed.
- `external_reference_needed`: outside information still needs to be reviewed.
- `not_supported_by_public_corpus`: the requested conclusion or disclosure cannot be supported publicly.

Explicit supplier, manufacturer, or proprietary-formula non-disclosure overrides a completed external review and routes back to the frontline pharmacist.

## Severe-trigger policy

- A listed severe trigger reported in the complaint, such as hospitalization, is proposed immediately for reviewer confirmation.
- Shortness of breath, collapse, and falling over remain clinical context unless another controlled severe trigger is present.
- Final escalation routing uses structured triggers rather than free-text keyword scanning.

## Review-scope defaults

For a full quality or ADE investigation:

- undocumented record review -> `documentation_incomplete`
- undocumented lot/batch result -> `unavailable`
- undocumented inventory inspection -> `not_checked`
- unmentioned reference review -> `not_needed`

For guidance-only work:

- irrelevant record, lot, and inventory fields -> `not_applicable`
- unmentioned reference review -> `not_needed`

Explicit reviewer findings always override these defaults.

## Retrieval baseline

The development retrieval benchmark is not yet stable:

- Hit rate@5: `0.75`
- Mean reciprocal rank: `0.5875`
- Negative-constraint pass rate: `0.85`
- Failed questions: `5`
- Forbidden-source hits: `3`

The next retrieval work is label correction, adverse-event query expansion/reranking, ingredient/disclosure retrieval support, and only then targeted SOP wording changes if a genuine source-truth gap remains.

## SOP status

No SOP or chunk content was changed during the recent extraction work.

Earlier retrieval work did make narrow corpus changes:

- `SOP-006`: explicit low-star/no-review-text document-only guidance.
- `SOP-005`: explicit unsupported product-specific stability boundary outside the limited temperature-excursion guidance.
- `SOP-006`: associated frontline/document-only routing language.

Do not change chunking or add broad SOP content merely to improve benchmark scores. Change source text only when the intended policy is genuinely absent or under-specified.
