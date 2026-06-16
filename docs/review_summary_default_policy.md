# Review Summary Default Policy

Status: confirmed

## Scope-first defaults

The extractor must not let the language model decide what silence means.

### Guidance-only cases

When record review, lot/batch review, or inventory inspection is not documented:

```yaml
record_review_result: not_applicable
lot_batch_pattern_summary: not_applicable
inventory_inspection_result: not_applicable
```

Examples include narrow ingredient questions, supplier-disclosure questions, storage questions without an observed defect or clinical event, and BUD guidance questions without a separate quality concern.

### Full quality or adverse-event investigations

When the investigation is required but the result is not documented:

```yaml
record_review_result: documentation_incomplete
lot_batch_pattern_summary: unavailable
inventory_inspection_result: not_checked
```

Examples include reported adverse events, physical product defects, actual device failures, quantity shortages, dispensing errors, and efficacy concerns tied to worsening clinical response.

Explicit documented findings override these defaults.

## Reference-review default

When reference review is not mentioned:

```yaml
api_reference_review_result: not_needed
```

Do not infer that a reference was consulted.

Use another value only when the investigation explicitly states that:

- a project reference was consulted;
- an external reference was consulted;
- an external reference is still needed; or
- the requested answer or disclosure is unsupported.

## Related extraction rules

- Product concentration and package quantity do not establish the administered dose.
- Numeric dose values require administration context such as `gave`, `administered`, `received`, `draws up`, or `per dose`.
- Device questions require actual failure context. Directions such as `2 clicks = 0.1 mL` do not by themselves imply a dispensing failure.
- Canonical unresolved items must remain relevant to the complaint being evaluated.
