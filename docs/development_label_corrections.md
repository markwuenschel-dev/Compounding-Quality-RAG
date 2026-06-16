# Development Label Corrections

Corrected cases: **8**

The holdout fixtures were not changed.

## Changes

### `DEV-EXT-004-PAIR-0022`

The note says USP guidance was incorporated. Under the proposed policy, a completed abstracted reference review is labeled synthetic_reference_consulted unless the note explicitly states that the requested conclusion is unsupported.

- `api_reference_review_result`: `not_supported_by_public_corpus` -> `synthetic_reference_consulted`
- `evidence_limitations`: `['Product-specific refrigerated stability is not supported by the public corpus.']` -> `[]`

### `DEV-EXT-007-PAIR-0036`

Hospitalization appears in the complaint but not in the canonical reviewer note. The extraction contract treats severe_triggers_observed as reviewer-confirmed findings, so complaint-only facts are not gold labels for reviewer-note extraction.

- `severe_triggers_observed`: `['pet_hospitalization']` -> `[]`

### `DEV-EXT-011-PAIR-0103`

The limitation now mirrors the supplied investigation instead of adding a public-corpus conclusion that the reviewer note did not state.

- `evidence_limitations`: `['The complete proprietary inactive-ingredient formula is not supported by the public corpus.']` -> `['The full proprietary formula was not disclosed.']`

### `DEV-EXT-012-PAIR-0106`

The limitation now mirrors the supplied investigation and preserves the explicit non-disclosure boundary.

- `evidence_limitations`: `['Specific supplier and manufacturer details are not supported by the public corpus.']` -> `['Specific supplier or manufacturer details were not disclosed.']`

### `DEV-EXT-014-PAIR-0157`

This is an adverse-event investigation, but the canonical reviewer note does not document record-review or lot-trend outcomes. Under the proposed silence policy, required-but-undocumented review maps to documentation_incomplete and unavailable rather than not_applicable.

- `record_review_result`: `not_applicable` -> `documentation_incomplete`
- `lot_batch_pattern_summary`: `not_applicable` -> `unavailable`

### `DEV-EXT-015-PAIR-0169`

This case includes a reported transdermal reaction and formulation concern. Record and lot review remain relevant, but their outcomes are not documented in the canonical investigation.

- `record_review_result`: `not_applicable` -> `documentation_incomplete`
- `lot_batch_pattern_summary`: `not_applicable` -> `unavailable`

### `DEV-EXT-016-PAIR-0187`

USP guidance was incorporated. The note does not explicitly state that the requested refrigerated-efficacy conclusion was unsupported.

- `api_reference_review_result`: `not_supported_by_public_corpus` -> `synthetic_reference_consulted`
- `evidence_limitations`: `['Product-specific efficacy after refrigeration is not supported by the public corpus.']` -> `[]`

### `DEV-EXT-019-PAIR-0295`

USP guidance was incorporated. The canonical reviewer note does not explicitly state that a degradation-rate answer was unsupported.

- `api_reference_review_result`: `not_supported_by_public_corpus` -> `synthetic_reference_consulted`
- `evidence_limitations`: `['A product-specific degradation rate after the beyond-use date is not supported by the public corpus.']` -> `[]`

## Still awaiting domain clarification

- Combined-solution dose uniformity: guidance-only or incomplete quality review?
- Respiratory distress: serious context only or a structured severe trigger?
- Collapse/falling over: serious context only or a structured severe trigger?
- Completed manufacturer/veterinary-reference review: keep mapped to `synthetic_reference_consulted` or add `external_reference_consulted`?
- Completed reference review plus non-disclosure: should the support boundary override the completed-review label?
