# Controlled Retrieval Intent Ablation

Updated: 2026-06-25

## Goal

Measure whether semantic query interpretation improves retrieval while holding the rest of the retrieval system constant.

```text
complaint -> semantic intent detector -> deterministic workflow derivation -> shared vocabulary mapper -> unchanged keyword retriever
```

Compared strategies:

1. `raw`
2. `deterministic_expansion`
3. `rule_intent`
4. `nano_intent`

The corpus, chunks, keyword retriever, scoring, `top_k`, expected sources, forbidden sources, deterministic policy, and shared mapper remain fixed.

## Why separate from retriever comparison

Retriever comparison asks which retriever performs best: keyword, local vector, or hybrid.

This ablation asks whether query interpretation improves retrieval while using the same retriever. Combining both variables would make the result difficult to interpret.

## Strategy definitions

### Raw

Original concern unchanged. Transparent control.

### Deterministic expansion

Original concern plus controlled legacy expansion concepts. Low-complexity comparator.

### Rule intent

`RuleIntentDetector` produces `SemanticRetrievalIntent`; deterministic policy derives `RetrievalIntent`; mapper produces final search text.

Properties:

- local;
- deterministic;
- negligible latency;
- no API dependency;
- suitable fallback;
- vulnerable to unfamiliar phrasing.

### Nano intent

GPT-5 Nano produces `SemanticRetrievalIntent`.

Nano returns semantic facts only. It does not emit workflow tags or final search text. Deterministic policy derives workflow consequences.

Properties:

- strongest measured frozen-holdout generalization;
- external API dependency;
- higher latency;
- cost;
- cache/fallback complexity.

## Intent contracts

Semantic contract:

```json
{"tags": ["adverse_event", "neurologic_signs"]}
```

Derived contract:

```text
Semantic facts -> deterministic workflow consequences -> corpus vocabulary -> keyword retrieval
```

Important boundary:

```text
Model: semantic facts only
Deterministic code: workflow consequences
Retriever: ranked source chunks
```

## Cache and fallback contract

Successful Nano output may be cached using:

```text
question ID + normalized concern SHA-256 + model name + intent schema version
```

If Nano returns invalid JSON, an unknown tag, validation failure, timeout, or provider error, the request falls back to rule intent.

Rule fallback output is not stored as a Nano prediction.

## Metrics

Retrieval:

- hit rate at K;
- mean reciprocal rank;
- negative-constraint pass rate;
- failed question IDs;
- forbidden-hit IDs;
- query-build/retrieval/total latency;
- model calls;
- cache hits/misses;
- fallbacks.

Intent metrics, when labels exist:

- semantic micro precision/recall/exact match;
- derived micro precision/recall/exact match;
- per-tag diagnostics.

Operational diagnostics:

- unknown tag count;
- unmapped tag count;
- structured-output failures;
- model errors/timeouts;
- fallbacks.

## Recorded evaluations

### Controlled intent challenge

Dataset: `data/eval/retrieval_intent_challenge.json`  
Questions: 14  
Top K: 5  
Nano: not used in recorded local challenge

| Strategy | Hit rate@5 | MRR | Negative pass |
|---|---:|---:|---:|
| Raw | 0.714 | 0.679 | 0.786 |
| Deterministic expansion | 0.714 | 0.643 | 0.786 |
| Rule intent | 1.000 | 1.000 | 1.000 |

Targeted challenge result does not establish production accuracy.

### Development retrieval evaluation

Dataset: `data/eval/retrieval_questions_development.json`  
Questions: 20  
Top K: 5  
Nano model: `gpt-5-nano`

| Strategy | Hit rate@5 | MRR | Negative pass |
|---|---:|---:|---:|
| Raw | 0.700 | 0.563 | 0.850 |
| Deterministic expansion | 1.000 | 0.804 | 0.900 |
| Rule intent | 1.000 | 0.950 | 1.000 |
| Nano intent | 0.900 | 0.900 | 1.000 |

Recorded uncached runtime:

| Strategy | Runtime |
|---|---:|
| Rule intent | ~0.026 seconds total |
| Nano intent | ~116.648 seconds for 20 calls |

Development set was used for error analysis and tuning.

### Frozen holdout retrieval evaluation

Dataset: `data/eval/retrieval_questions_holdout.json`  
Questions: 20  
Top K: 5  
Nano model: `gpt-5-nano`

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
total uncached runtime: ~103.361 seconds
```

Nano missed:

```text
HOLD-RET-001-PAIR-0039
```

## Interpretation

Nano is the current accuracy-oriented winner, with latency/cost/dependency tradeoffs.

Rule intent is the deterministic fallback.

Deterministic expansion and raw query remain comparators.

Keyword retrieval remains the unchanged retriever after query interpretation.

## Commands

From `rag-engine-python`.

```powershell
uv run python -m app.holdout_evaluate retrieval-ablation `
  --questions data/eval/retrieval_questions_holdout.json `
  --strategies raw,deterministic_expansion,rule_intent,nano_intent `
  --run-id retrieval-intent-holdout-v4 `
  --refresh-nano
```

## Holdout policy

The recorded v4 holdout is the frozen generalization baseline.

If future fixes use its failures, this dataset becomes a regression benchmark. New generalization claims require a new untouched holdout.

## Runtime decision

Current accuracy path:

```text
Nano semantic intent -> deterministic workflow derivation -> vocabulary mapper -> keyword retrieval
```

Failure path:

```text
Rule semantic intent -> deterministic workflow derivation -> vocabulary mapper -> keyword retrieval
```

Preserve raw and deterministic expansion as comparators.

## Current milestone status

Retrieval experimentation is closed for the current product milestone.

Further Nano optimization belongs in a later performance milestone:

- latency reduction;
- cache tuning;
- fallback-rate monitoring;
- model-cost tracking;
- larger holdout expansion.

Current product milestone is operational hardening:

- GitHub Actions for Python, Spring Boot, React, and repo checks;
- health/readiness smoke tests against running containers;
- `.env.example`;
- runbook maintenance;
- structured operation logs beyond request correlation with operation names, duration, model, cache, fallback, and bounded error fields.

Docker Compose, HTTP service boundary, and request correlation are already implemented and should not be listed as future work.
