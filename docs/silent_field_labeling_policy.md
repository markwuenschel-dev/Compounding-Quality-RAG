# Proposed Silent-Field Labeling Policy

## Record review

- Explicit normal result -> `no_discrepancy_found`
- Explicit discrepancy -> `documentation_discrepancy_found`
- Explicitly incomplete review, or a required quality/ADE review whose result
  is absent from the canonical investigation -> `documentation_incomplete`
- Guidance-only case where record review is irrelevant -> `not_applicable`

## Lot or batch review

- Explicit no-pattern result -> `no_similar_batch_concerns_found`
- Explicit matching pattern -> the corresponding similar-concern value
- Review is relevant but no result is documented -> `unavailable`
- Guidance-only case where lot review is irrelevant -> `not_applicable`

## Inventory inspection

- Explicit no retained inventory -> `no_inventory_available`
- Explicit inspection without concern -> `no_visual_concern_found`
- Explicit inspection with concern -> `visual_concern_found`
- Inspection is relevant but no result is documented -> `not_checked`
- Guidance-only case or no physical-product question -> `not_applicable`

These rules prevent `not_applicable` from being used as a generic substitute
for an undocumented review result.
