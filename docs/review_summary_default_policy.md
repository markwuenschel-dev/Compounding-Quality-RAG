# Review Summary Default Policy

Status: confirmed  
Updated: 2026-06-25

## Purpose

The extractor must not let the language model decide what silence means.

A missing review-summary field can mean:

1. the field is irrelevant to a guidance-only question;
2. the field is required but the review result was not documented.

This policy defines deterministic defaults after LLM candidate extraction and Pydantic validation.

## Scope-first defaults

### Guidance-only cases

When record review, lot/batch review, or inventory inspection is not documented because the case is guidance-only:

```yaml
record_review_result: not_applicable
lot_batch_pattern_summary: not_applicable
inventory_inspection_result: not_applicable
api_reference_review_result: not_needed
```

Examples:

- narrow ingredient questions;
- supplier/manufacturer disclosure questions;
- storage questions without observed defect or clinical event;
- BUD guidance questions without separate quality concern;
- frontline pharmacist guidance questions without ADE, product-defect, dispensing-error, or severe-trigger facts.

### Full quality or adverse-event investigations

When investigation is required but result is not documented:

```yaml
record_review_result: documentation_incomplete
lot_batch_pattern_summary: unavailable
inventory_inspection_result: not_checked
api_reference_review_result: not_needed
```

Examples:

- reported adverse events;
- physical product defects;
- actual device failures;
- quantity shortages;
- dispensing errors;
- efficacy concerns tied to worsening clinical response;
- combined-product dose-uniformity concerns linked to clinical worsening or lack of therapeutic response.

Explicit documented findings override these defaults.

## Reference-review default

When reference review is not mentioned:

```yaml
api_reference_review_result: not_needed
```

Do not infer that a reference was consulted.

Use another value only when the investigation explicitly states that:

- a synthetic/project reference was consulted;
- an external reference was consulted;
- an external reference is still needed;
- the requested answer or disclosure is unsupported by the public corpus.

Reference precedence:

1. unsupported or non-disclosable;
2. completed external review;
3. completed synthetic-corpus review;
4. external review still needed;
5. no reference review needed.

## Severe-trigger relationship

Review-scope defaults do not create severe triggers.

Severe triggers must come from structured trigger handling:

```yaml
severe_triggers_observed:
  - pet_hospitalization
```

Negated language such as `no hospitalization` must not populate severe triggers.

## Related extraction rules

- Product concentration and package quantity do not establish administered dose.
- Numeric dose values require administration context such as `gave`, `administered`, `received`, `draws up`, or `per dose`.
- Device questions require actual failure context.
- Directions such as `2 clicks = 0.1 mL` do not by themselves imply a dispensing failure.
- `Confirm`, `Clarify`, and `Determine whether` introduce unresolved information when decision-relevant.
- Canonical unresolved items must remain relevant to the complaint.
- Supplier/manufacturer/proprietary non-disclosure maps to `not_supported_by_public_corpus` even if outside information was reviewed.

## Testing expectations

Keep paired tests for:

- guidance-only silence;
- full-investigation silence;
- explicit normal record review;
- explicit incomplete review;
- lot-pattern positive/negative findings;
- no inventory available;
- inventory not checked;
- reference review not mentioned;
- completed external reference review;
- non-disclosure overriding completed external review.
