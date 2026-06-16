# Holdout Evaluation Case Authoring

This scaffold creates two independent, frozen datasets:

1. **Narrative extraction holdout** — tests whether messy pharmacist notes become the correct structured review summary.
2. **Retrieval relevance holdout** — tests whether a customer concern retrieves the right SOP source and avoids known irrelevant sources.

Do not run the model against candidate cases while expected answers are still being written. Define the expected result first, review it for ambiguity, then freeze the files.

## Data boundary

Use synthetic or fully de-identified text only. Do not paste real customer, patient, prescription, order, compounding-record, inventory, or protected operational data into the repository or model workflow.

## Narrative extraction fixture

Edit:

```text
rag-engine-python/data/eval/review_summary_extraction_holdout.json
```

Each case uses the existing extraction-evaluation contract:

```json
{
  "case_id": "EXT-H-001",
  "concern_text": "Synthetic customer concern.",
  "reviewer_note": "Messy synthetic pharmacist investigation note.",
  "expected_review_summary": {
    "record_review_result": "no_discrepancy_found",
    "lot_batch_pattern_summary": "unavailable",
    "inventory_inspection_result": "not_checked",
    "customer_context_summary": "Neutral factual summary or null.",
    "api_reference_review_result": "not_needed",
    "missing_information": [],
    "evidence_limitations": [],
    "severe_triggers_observed": []
  },
  "expected_unresolved_field_names": []
}
```

### Authoring rules

- Use the canonical enum values already defined in `app/schemas.py`.
- Put only explicitly unresolved facts in `missing_information`.
- Put unavailable verification paths in `evidence_limitations`.
- Add a severe trigger only when the pharmacist note affirmatively supports it.
- Use field names, not full question text, in `expected_unresolved_field_names`.
- Preserve contradictions and uncertainty in the messy note instead of cleaning them up.
- Mark a case for discussion rather than forcing a single expected answer when two reasonable pharmacists would disagree.

### Useful case types

- misspellings and shorthand
- vague pronouns
- conflicting dose or timing statements
- customer allegation later ruled out by the reviewer
- hospitalization negation
- veterinarian contact without an allegation of harm
- possible contamination later ruled out
- wrong-medication concern later confirmed correct
- multiple symptoms or multiple products
- incomplete investigation
- device issue mixed with a possible adverse event
- irrelevant narrative details
- explicit external-reference limitation

## Retrieval holdout fixture

Edit:

```text
rag-engine-python/data/eval/retrieval_questions_holdout.json
```

Each question supports positive and negative relevance expectations:

```json
{
  "question_id": "RET-H-001",
  "query": "Synthetic customer concern used as the retrieval query.",
  "expected_source_ids": ["SOP-005"],
  "forbidden_source_ids": ["SOP-002"],
  "rationale": "Adverse-event guidance should rank; BUD guidance is irrelevant."
}
```

### Authoring rules

- `expected_source_ids` means any listed source is a relevant hit.
- `forbidden_source_ids` identifies a known misleading source that should not enter top K.
- Do not forbid a source merely because another source is better.
- Base source expectations on the corpus content, not on the current ranking.
- Use the customer’s natural wording, including noise and shorthand.
- Record a rationale before running retrieval.

### Useful retrieval cases

- vomiting after oral liquid where shortage guidance is irrelevant
- flavor refusal without vomiting
- BUD clarification
- transdermal pen leakage or failure to dispense
- possible wrong patient or wrong medication
- contamination allegation
- temperature excursion requiring an external reference boundary
- multiple concerns in one submission
- vague query with one decisive domain term

## Candidate-case worksheet

Use `docs/holdout_case_capture_worksheet.md` while collecting and reviewing candidates. Transfer only adjudicated cases into the JSON files.

## Validation and freezing

Before the first model run:

```powershell
cd rag-engine-python
python -m app.holdout_evaluate validate
python -m app.holdout_evaluate freeze
```

The freeze command writes:

```text
rag-engine-python/data/eval/holdout_manifest.json
```

Commit the fixtures and manifest before tuning. The SHA-256 hashes make later fixture changes visible.

## Baseline runs

Retrieval does not require an OpenAI call:

```powershell
python -m app.holdout_evaluate retrieval
```

Narrative extraction uses the configured OpenAI client:

```powershell
python -m app.holdout_evaluate extraction
```

Run both:

```powershell
python -m app.holdout_evaluate all
```

Generated reports:

```text
rag-engine-python/reports/retrieval_holdout.md
rag-engine-python/reports/review_summary_extraction_holdout.md
```

## Failure classification

Before changing code, classify each failure as one of:

- extraction prompt failure
- deterministic grounding failure
- schema or contract failure
- retrieval scoring failure
- missing corpus guidance
- chunk-boundary failure
- ambiguous or incorrect expected answer

Change only the layer responsible for the observed failure.
