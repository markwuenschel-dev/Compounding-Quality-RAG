# Review Summary Extraction Evaluation

Generated: `2026-06-14T15:09:28Z`
Case count: `6`

## Summary

| Metric | Score |
|---|---:|
| Scalar field accuracy | 1.000 |
| Missing-information precision | 1.000 |
| Missing-information recall | 1.000 |
| Severe-trigger precision | 1.000 |
| Severe-trigger recall | 1.000 |
| Unresolved-question precision | 1.000 |
| Unresolved-question recall | 1.000 |

## Failed cases

None

## Guardrails

- Severe-trigger false positives and false negatives require manual review.
- Numeric model confidence is intentionally not reported because it has not been calibrated.
- Supporting quotes must come directly from the reviewer note.
- This evaluation uses synthetic cases and does not establish production clinical performance.
