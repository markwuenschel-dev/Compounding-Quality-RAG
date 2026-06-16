# Customer Complaint Prompt Ingestion

- Parsed rows: **513**
- Ignored rows containing phone/contact information: **59**
- Canonical candidates created: **382**
- Exact duplicates collapsed: **2**
- Low-information rows excluded: **70**
- Canonical archetypes represented: **52**

## Files

- `customer_complaint_prompt_candidates.csv` — review and adjudication sheet.
- `customer_complaint_prompt_candidates.json` — structured candidate data.
- `canonical_prompt_archetypes.json` — reusable prompt archetypes with observed counts.

## Candidate fields

- `canonical_concern` is the cleaned complaint text suitable for retrieval input.
- `evaluation_prompt` wraps the concern in a consistent review instruction.
- `expected_source_ids` and `forbidden_source_ids` are blank until adjudication.
- `source_rows` and `source_fingerprint` preserve traceability without copying ignored contact rows.

## Largest issue groups

- `GENERAL_COMPOUNDING_QUESTION`: 26
- `ADE_GASTROINTESTINAL`: 22
- `PALATABILITY_ORAL_REACTION`: 17
- `EFFICACY_SUSPECTED_PRODUCT_FAILURE`: 17
- `BUD_EXPIRATION_OR_STABILITY`: 15
- `DEVICE_GENERAL`: 13
- `INGREDIENT_ALLERGEN_OR_EXCIPIENT`: 12
- `QUANTITY_VISUAL_UNDERFILL`: 11
- `QUANTITY_GENERAL`: 11
- `QUANTITY_RUNS_OUT_EARLY`: 11
- `QUALITY_ODOR_OR_FLAVOR_CHANGE`: 11
- `QUALITY_CLOUDY_OR_COLOR_CHANGE`: 10
- `ADE_NEURO_BEHAVIORAL`: 9
- `ADE_DERMAL_APPLICATION_SITE`: 9
- `INGREDIENT_SOURCE_OR_MANUFACTURER`: 9
