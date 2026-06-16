# Investigation Prompt Ingestion

- Investigation records parsed: **513**
- Complaint/investigation pairs created: **382**
- Empty file rows ignored: **2**
- Canonical duplicates retained for order alignment: **162**
- Investigation archetypes represented: **13**

## Redactions removed from generated artifacts

- `email_addresses`: 14
- `formatted_phone_numbers`: 24
- `names_in_role_context`: 19
- `operational_identifiers`: 96
- `plain_phone_numbers`: 56
- `street_addresses`: 7
- `urls`: 5

## Files

- `investigation_prompt_candidates.csv` — all investigations in source order.
- `investigation_prompt_candidates.json` — structured all-row candidate data.
- `paired_case_candidates.csv` — the existing complaint candidate set joined to its same-position investigation.
- `paired_case_candidates.json` — structured paired candidate data.
- `investigation_archetypes.json` — archetype counts for selection and balancing.

## Largest investigation groups

- `DEVICE_OR_DISPENSING_REVIEW`: 138
- `INGREDIENT_OR_ALLERGEN_REVIEW`: 87
- `OTHER_INVESTIGATION`: 65
- `ADVERSE_EVENT_REVIEW`: 49
- `STORAGE_OR_TEMPERATURE_REVIEW`: 33
- `DOSING_OR_ADMINISTRATION_REVIEW`: 30
- `PALATABILITY_REVIEW`: 21
- `QUANTITY_OR_DAY_SUPPLY_REVIEW`: 18
- `BUD_OR_LABEL_REVIEW`: 18
- `EXTERNAL_PRODUCT_ROUTING`: 16
- `APPEARANCE_OR_UNIFORMITY_REVIEW`: 13
- `AVAILABILITY_OR_FORMULATION_REQUEST`: 13
- `RECORD_DEVIATION_FOUND`: 12
