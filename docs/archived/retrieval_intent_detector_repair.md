# Retrieval Intent Detector Repair

## Scope

This work repaired semantic intent detection, deterministic policy derivation, retrieval evaluation, and cache provenance without changing:

- the SOP corpus;
- chunk generation;
- keyword scoring;
- `top_k`;
- expected source labels;
- forbidden source labels;
- Spring Boot endpoints;
- the React workflow.

## Final Architecture

```text
complaint
→ semantic intent detector
→ deterministic workflow derivation
→ shared deterministic vocabulary mapper
→ unchanged keyword retriever
```

Supported semantic detectors:

- `RuleIntentDetector`
- `NanoIntentDetector`

Both return `SemanticRetrievalIntent`.

`derive_retrieval_intent()` converts semantic facts into deterministic workflow and retrieval-policy tags. `map_intent_to_search_text()` then maps those tags into corpus-aligned search vocabulary.

## Repaired Defects

### Quantity discrepancy workflow

A quantity discrepancy previously added `quality_review` without the mandatory `trend_review`.

The corrected path uses the shared full-quality-review helper, which adds:

```text
quality_review
trend_review
```

Quantity discrepancy also derives `administration_review`.

### Nano semantic-only vocabulary

Nano was previously prompted with the full derived `RetrievalIntentTag` vocabulary.

The corrected prompt lists only `SemanticIntentTag` values.

Nano cannot directly return workflow tags such as:

```text
quality_review
trend_review
administration_review
reference_review
disclosure_boundary
```

The model identifies semantic facts. Deterministic code owns workflow consequences.

### Semantic metric repair

`calculate_semantic_intent_metrics()` now evaluates:

```text
predicted_semantic_intent_tags
expected_semantic_intent_tags
semantic_intent_exact_match
```

against the `SemanticIntentTag` vocabulary.

Derived intent is scored separately.

### Cache provenance repair

Only successful Nano predictions are cached.

```text
successful Nano output
→ validate
→ cache as Nano
```

```text
Nano failure
→ rule fallback
→ return fallback result
→ do not cache as Nano
```

This prevents rule output from being stored under Nano's model identity and ensures Nano may be retried later.

### Cache contract migration

The cache stores `SemanticRetrievalIntent` through:

```python
semantic_intent=...
```

Stale callers using `intent=` and old `RetrievalIntent` values were migrated.

### Evaluation contract repair

`RetrievalHoldoutQuestion` now supports:

```text
expected_semantic_intent_tags
expected_intent_tags
```

Semantic labels are validated with `SemanticRetrievalIntent`.

Derived labels are validated with `RetrievalIntent`.

### Supplier-language generalization

The development set exposed this phrasing:

```text
ask about where we source the ingredients from
```

The information-request vocabulary already recognized `asking about` and `asked about`, but not:

```text
ask about
asks about
```

Those grammatical forms were added while preserving the two-part supplier detector contract:

1. supplier, manufacturer, source, or ingredient-source language must be present;
2. explicit information-seeking language must also be present.

This is a bounded language-normalization change rather than a broad supplier keyword shortcut.

## Matching Rules

- Short tokens such as `pen` use word-boundary matching.
- Supplier intent requires supplier/manufacturer/source language plus information-seeking context.
- Manufacturer reporting language does not imply a supplier-information request.
- Administration questions are separated from administration timing context.
- Ingredient composition requests are separated from palatability complaints.
- `device_review` is not used because it is not a canonical workflow concept.
- Every full quality review includes trend review.
- Workflow tags are derived from semantic evidence rather than emitted by Nano.
- Fallback output is not cached as Nano output.

## Recorded Results

### Controlled challenge — 14 questions

| Strategy | Hit rate@5 | MRR | Negative pass |
|---|---:|---:|---:|
| Raw | 0.714 | 0.679 | 0.786 |
| Deterministic expansion | 0.714 | 0.643 | 0.786 |
| Rule intent | 1.000 | 1.000 | 1.000 |

Rule intent semantic and derived exact match were both `1.000`.

### Development — 20 questions

| Strategy | Hit rate@5 | MRR | Negative pass |
|---|---:|---:|---:|
| Raw | 0.700 | 0.563 | 0.850 |
| Deterministic expansion | 1.000 | 0.804 | 0.900 |
| Rule intent | 1.000 | 0.950 | 1.000 |
| Nano intent | 0.900 | 0.900 | 1.000 |

### Frozen holdout — 20 questions

| Strategy | Hit rate@5 | MRR | Negative pass |
|---|---:|---:|---:|
| Raw | 0.700 | 0.567 | 0.850 |
| Deterministic expansion | 0.850 | 0.733 | 0.850 |
| Rule intent | 0.750 | 0.725 | 0.900 |
| Nano intent | 0.950 | 0.950 | 1.000 |

The frozen holdout establishes Nano as the strongest measured generalization path. Rule intent remains the fast deterministic fallback.

## Runtime Decision

Primary accuracy path:

```text
Nano semantic intent
→ deterministic workflow derivation
→ shared vocabulary mapper
→ keyword retrieval
```

Failure path:

```text
Nano failure or timeout
→ rule semantic intent
→ deterministic workflow derivation
→ shared vocabulary mapper
→ keyword retrieval
```

Only successful Nano semantic predictions are cached as Nano output.

## Validation

Focused checks:

```powershell
uv run pytest `
  tests/test_retrieval_intent.py `
  tests/test_retrieval_intent_keyword_integration.py `
  tests/test_retrieval_query_strategy.py `
  tests/test_retrieval_ablation.py `
  tests/test_holdout_evaluate.py
```

Full checks:

```powershell
uv run pytest
uv run mypy app tests
uv run pyright app tests
uv run ruff check .
```

## Holdout Guardrail

The recorded v4 holdout remains the frozen generalization baseline.

Once future changes are designed using its failures, it becomes a regression benchmark rather than an unbiased holdout. New generalization claims require a new untouched holdout.
