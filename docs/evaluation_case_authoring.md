# Holdout and Evaluation Case Authoring

Updated: 2026-06-25

This document explains how to author new synthetic evaluation cases without contaminating baselines.

## Evaluation lanes

1. **Narrative extraction** — messy complaint/reviewer notes become correct structured `ReviewSummary`.
2. **Retrieval relevance** — customer concerns retrieve relevant SOP-like sources and avoid known misleading sources.
3. **Retrieval intent** — semantic facts and derived workflow tags are correct when adjudicated labels exist.

## Core rule

Do not run the model against candidate cases while expected answers are still being written.

Correct order:

```text
write candidate -> write expected answer -> adjudicate ambiguity -> freeze fixture -> run evaluator -> classify failures -> change only the responsible layer
```

A model result must not influence the first expected answer.

## Data boundary

Use only synthetic or fully de-identified text.

Do not paste real customer, patient, veterinarian, prescription, order, compounding-record, inventory, employee, proprietary SOP, internal-system, or protected operational data into repository files, model prompts, evaluation fixtures, screenshots, or docs.

## Dataset roles

| Dataset | Purpose | May guide fixes? |
|---|---|---:|
| Development | Tuning and error analysis | Yes |
| Frozen holdout | Generalization estimate | No, until after the reported run |
| Regression benchmark | Prevent known failures returning | Yes |
| Challenge set | Targeted mechanism proof | Yes, but not a generalization claim |

Once holdout results guide a fix, that holdout becomes a regression benchmark. New generalization claims require a new untouched holdout.

## Narrative extraction fixture

Example shape:

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

- Use canonical enum values from `app/schemas.py` and `docs/data_dictionary.md`.
- Preserve messy wording, abbreviations, contradictions, and uncertainty.
- Do not over-clean notes.
- Put only explicitly unresolved facts in `missing_information`.
- Put unavailable verification paths in `evidence_limitations`.
- Use field names, not full generated question text, in `expected_unresolved_field_names`.
- Add severe triggers only under the reported-trigger policy.
- Mark ambiguous cases for discussion instead of forcing a questionable label.

### Useful extraction cases

- misspellings and shorthand;
- vague pronouns;
- conflicting dose/timing statements;
- strength or package quantity that is not administered dose;
- hospitalization negation;
- complaint-reported hospitalization requiring confirmation;
- possible contamination later ruled out;
- wrong-medication concern later confirmed correct;
- device issue mixed with possible ADE;
- incomplete investigation;
- supplier/manufacturer/proprietary non-disclosure.

## Retrieval fixture

Example shape:

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

- `expected_source_ids` means any listed source is relevant.
- `forbidden_source_ids` identifies a materially misleading source that should not enter top K.
- Do not forbid a source merely because another source is better.
- Base expectations on corpus content, not current ranking.
- Use natural customer wording, including noise.
- Record rationale before running retrieval.
- If the corpus lacks the intended policy, classify as missing corpus guidance rather than retriever failure.

## Optional intent labels

Current development/holdout retrieval datasets mainly evaluate retrieval behavior. Semantic and derived metric fields may remain null when no adjudicated labels exist.

For future intent-labeled cases:

```json
{
  "expected_semantic_intent_tags": ["adverse_event"],
  "expected_intent_tags": ["quality_review", "trend_review"]
}
```

Rules:

- semantic tags describe facts in the concern;
- derived tags describe deterministic workflow consequences;
- the model should not directly emit workflow tags.

## Validation and freezing

```powershell
cd rag-engine-python
uv run python -m app.holdout_evaluate validate
uv run python -m app.holdout_evaluate freeze
```

The freeze command writes/updates:

```text
rag-engine-python/data/eval/holdout_manifest.json
```

Commit fixtures and manifest before tuning.

## Baseline runs

```powershell
cd rag-engine-python
uv run python -m app.holdout_evaluate retrieval
uv run python -m app.holdout_evaluate extraction
uv run python -m app.holdout_evaluate all
```

Retrieval intent ablation:

```powershell
uv run python -m app.holdout_evaluate retrieval-ablation `
  --questions data/eval/retrieval_questions_holdout.json `
  --strategies raw,deterministic_expansion,rule_intent,nano_intent `
  --run-id retrieval-intent-holdout-vNEXT `
  --refresh-nano
```

## Failure classification

Before changing code, classify the failure:

- extraction prompt failure;
- deterministic grounding failure;
- review-scope default failure;
- unresolved-question generation failure;
- schema or contract failure;
- retrieval scoring/ranking failure;
- semantic intent detection failure;
- deterministic workflow derivation failure;
- vocabulary mapping failure;
- cache/fallback provenance failure;
- missing corpus guidance;
- chunk-boundary failure;
- ambiguous or incorrect expected answer;
- public-boundary/refusal failure.

Change only the responsible layer.

## Reporting rule

Always distinguish:

- development performance;
- frozen-holdout performance;
- targeted challenge performance;
- regression benchmark performance.

Never summarize a development result as production accuracy.
