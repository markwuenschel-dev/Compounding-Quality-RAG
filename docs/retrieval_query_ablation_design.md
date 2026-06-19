# Controlled Retrieval Intent Ablation

## Goal

Measure whether semantic query interpretation improves retrieval while holding the rest of the retrieval system constant.

```text
complaint
→ semantic intent detector
→ deterministic workflow derivation
→ shared deterministic vocabulary mapper
→ unchanged keyword retriever
```

The compared strategies are:

1. `raw`
2. `deterministic_expansion`
3. `rule_intent`
4. `nano_intent`

The corpus, chunks, keyword retriever, scoring, `top_k`, expected sources, forbidden sources, deterministic policy, and shared mapper remain fixed within each comparison.

## Why This Is Separate from Retriever Comparison

Retriever comparison asks which retrieval implementation performs best:

- keyword;
- local embedding;
- hybrid.

This ablation asks whether changing query interpretation improves retrieval while using the same retriever.

Combining both variables in one experiment would make the result difficult to interpret.

## Strategy Definitions

### Raw

Uses the original concern unchanged.

This is the transparent control.

### Deterministic expansion

Keeps the original concern and appends controlled concepts using the legacy expansion rules.

This remains a low-complexity comparator.

### Rule intent

Uses `RuleIntentDetector` to produce `SemanticRetrievalIntent`.

Deterministic policy then derives `RetrievalIntent`, and the shared mapper produces the final search text.

Properties:

- local;
- deterministic;
- negligible latency;
- no external API dependency;
- suitable fallback;
- vulnerable to unfamiliar phrasing.

### Nano intent

Uses GPT-5 Nano to produce `SemanticRetrievalIntent`.

Nano returns semantic facts only. It does not emit workflow tags or final search text.

Deterministic policy derives workflow consequences, and the same shared mapper produces the final search text.

Properties:

- strongest measured frozen-holdout generalization;
- external API dependency;
- materially higher latency;
- model cost;
- cache and fallback complexity.

## Intent Contracts

### Semantic contract

`SemanticRetrievalIntent` contains only `SemanticIntentTag` values.

Example:

```json
{"tags": ["adverse_event", "neurologic_signs"]}
```

Unknown tags fail validation.

### Derived contract

`derive_retrieval_intent()` adds deterministic workflow consequences such as:

- quality review;
- trend review;
- adverse-event review;
- pharmacist outreach;
- disclosure boundaries;
- public-corpus boundaries;
- reference review;
- reference boundaries.

The resulting `RetrievalIntent` is passed to `map_intent_to_search_text()`.

## Cache and Fallback Contract

Successful Nano output may be cached using:

```text
question ID
+ normalized concern SHA-256
+ model name
+ intent schema version
```

If Nano returns invalid JSON, an unknown tag, a validation failure, or a provider error, the request falls back to the rule detector.

Rule fallback output is not stored as a Nano prediction. This preserves provenance and allows a later request to retry Nano.

## Metrics

### Retrieval

- hit rate at K;
- mean reciprocal rank;
- negative-constraint pass rate;
- failed question IDs;
- forbidden-hit question IDs;
- query-build latency;
- retrieval latency;
- total latency;
- model calls;
- cache hits and misses;
- fallbacks.

### Semantic intent

Available when expected semantic labels are present:

- micro precision;
- micro recall;
- exact-match rate;
- per-semantic-tag precision and recall.

### Derived intent

Available when expected derived labels are present:

- micro precision;
- micro recall;
- exact-match rate;
- per-derived-tag precision and recall.

### Operational diagnostics

- unknown tag count;
- unmapped tag count;
- structured-output failure count;
- model error count.

The development and frozen-holdout datasets currently evaluate retrieval behavior only. Their semantic and derived metric fields remain null because they do not contain adjudicated intent labels.

## Recorded Evaluations

### Controlled intent challenge

Dataset:

```text
data/eval/retrieval_intent_challenge.json
```

Configuration:

```text
questions: 14
top_k: 5
intent schema: 4
Nano: not used in the recorded local challenge run
```

Results:

| Strategy | Hit rate@5 | MRR | Negative pass |
|---|---:|---:|---:|
| Raw | 0.714 | 0.679 | 0.786 |
| Deterministic expansion | 0.714 | 0.643 | 0.786 |
| Rule intent | 1.000 | 1.000 | 1.000 |

Rule intent also achieved:

| Intent metric | Result |
|---|---:|
| Semantic micro precision | 1.000 |
| Semantic micro recall | 1.000 |
| Semantic exact match | 1.000 |
| Derived micro precision | 1.000 |
| Derived micro recall | 1.000 |
| Derived exact match | 1.000 |

This fixture is a targeted challenge set and does not establish production accuracy.

### Development retrieval evaluation

Dataset:

```text
data/eval/retrieval_questions_development.json
```

Configuration:

```text
questions: 20
top_k: 5
intent schema: 4
Nano model: gpt-5-nano
```

Final results after the development-only supplier-language repair:

| Strategy | Hit rate@5 | MRR | Negative pass |
|---|---:|---:|---:|
| Raw | 0.700 | 0.563 | 0.850 |
| Deterministic expansion | 1.000 | 0.804 | 0.900 |
| Rule intent | 1.000 | 0.950 | 1.000 |
| Nano intent | 0.900 | 0.900 | 1.000 |

Recorded uncached runtime:

| Strategy | Runtime |
|---|---:|
| Rule intent | approximately 0.026 seconds total |
| Nano intent | approximately 116.648 seconds for 20 calls |

The development set was used for error analysis and tuning.

### Frozen holdout retrieval evaluation

Dataset:

```text
data/eval/retrieval_questions_holdout.json
```

Configuration:

```text
questions: 20
top_k: 5
intent schema: 4
Nano model: gpt-5-nano
```

Results:

| Strategy | Hit rate@5 | MRR | Negative pass |
|---|---:|---:|---:|
| Raw | 0.700 | 0.567 | 0.850 |
| Deterministic expansion | 0.850 | 0.733 | 0.850 |
| Rule intent | 0.750 | 0.725 | 0.900 |
| Nano intent | 0.950 | 0.950 | 1.000 |

Nano diagnostics:

```text
failed questions: 1
forbidden-hit questions: 0
model calls: 20
cache hits: 0
cache misses: 20
fallbacks: 0
structured-output failures: 0
model errors: 0
unknown tags: 0
unmapped tags: 0
total uncached runtime: approximately 103.361 seconds
```

Nano missed:

```text
HOLD-RET-001-PAIR-0039
```

The holdout establishes Nano as the strongest measured generalization path in the current corpus and evaluation.

## Interpretation

### Nano intent

Current accuracy-oriented winner:

- highest frozen-holdout hit rate;
- highest frozen-holdout MRR;
- perfect frozen-holdout negative-constraint pass rate;
- no output-validation or model failures in the recorded run.

Tradeoffs:

- external API dependency;
- materially higher latency;
- model cost;
- cache and fallback complexity.

### Rule intent

Current local deterministic fallback:

- negligible latency;
- no model dependency;
- perfect targeted challenge result;
- perfect development hit rate and negative pass after development tuning;
- weaker frozen-holdout generalization than Nano.

### Deterministic expansion

Retained as a low-complexity comparator.

It improved frozen-holdout hit rate relative to raw retrieval but did not match Nano's rank quality or negative-constraint behavior.

### Raw

Retained as the transparent baseline.

## Commands

From `rag-engine-python`.

Challenge:

```powershell
uv run python -m app.holdout_evaluate retrieval-ablation `
  --questions data/eval/retrieval_intent_challenge.json `
  --strategies raw,deterministic_expansion,rule_intent `
  --run-id retrieval-intent-challenge-local
```

Development:

```powershell
uv run python -m app.holdout_evaluate retrieval-ablation `
  --questions data/eval/retrieval_questions_development.json `
  --strategies raw,deterministic_expansion,rule_intent,nano_intent `
  --run-id retrieval-intent-development-v4 `
  --refresh-nano
```

Frozen holdout:

```powershell
uv run python -m app.holdout_evaluate retrieval-ablation `
  --questions data/eval/retrieval_questions_holdout.json `
  --strategies raw,deterministic_expansion,rule_intent,nano_intent `
  --run-id retrieval-intent-holdout-v4 `
  --refresh-nano
```

## Holdout Policy

The recorded v4 holdout is the frozen generalization baseline.

Future fixes may be informed by its failures, but after that happens this dataset must be treated as a regression benchmark. New generalization claims require a new untouched holdout.

## Decision

Preserve:

- Nano as the strongest measured generalization path;
- rule intent as the deterministic fallback;
- deterministic workflow derivation;
- shared corpus vocabulary mapping;
- keyword retrieval;
- deterministic expansion and raw query as comparators.

Retrieval experimentation is closed for the current product milestone. Further Nano optimization belongs in a later performance milestone.

The next product milestone is operational hardening:

- CI;
- Docker Compose;
- structured logging;
- readiness verification;
- environment configuration;
- operational runbook;
- end-to-end smoke testing.
