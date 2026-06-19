# Controlled Retrieval Intent Ablation

## Goal

Separate complaint understanding from workflow policy and corpus-specific search vocabulary.

```text
Complaint
→ semantic intent detector
→ deterministic workflow derivation
→ shared deterministic vocabulary mapper
→ unchanged keyword retriever
```

The experiment compares:

1. `raw`
2. `deterministic_expansion`
3. `rule_intent`
4. `nano_intent`

The legacy deterministic strategy remains unchanged as a comparator. Rule and nano detectors return `SemanticRetrievalIntent`. Deterministic policy derives `RetrievalIntent`, and both intent strategies use `map_intent_to_search_text`.

## Controlled variables

Do not change the SOP corpus, chunks, keyword scoring, `top_k`, expected source labels, or forbidden source labels during this experiment.

## Intent contracts

`SemanticRetrievalIntent` contains only evidence-level `SemanticIntentTag` values. Nano returns only semantic facts:

```json
{"tags": ["adverse_event", "neurologic_signs"]}
```

Nano does not generate workflow tags or final search text. Unknown tags fail validation and fall back to the rule detector for that request. Fallback output is not stored as a Nano prediction.

`derive_retrieval_intent` deterministically adds workflow consequences such as review, escalation, outreach, disclosure, trend, and reference boundaries. `RetrievalIntent` is then mapped to search vocabulary.

## Metrics

Retrieval:

- hit rate at K
- mean reciprocal rank
- negative-constraint pass rate
- failed question IDs
- forbidden-hit question IDs
- latency, model calls, cache hits, and fallbacks

Semantic intent:

- micro precision
- micro recall
- exact-match rate
- per-semantic-tag precision and recall

Derived intent:

- micro precision
- micro recall
- exact-match rate
- per-derived-tag precision and recall

Operational diagnostics:

- unknown tag count
- unmapped tag count
- structured-output failure count
- model error count

## Commands

From `rag-engine-python`:

```bash
uv sync --dev
uv run pytest
uv run python -m app.holdout_evaluate retrieval-ablation \
  --questions data/eval/retrieval_intent_challenge.json \
  --strategies raw,deterministic_expansion,rule_intent,nano_intent \
  --run-id retrieval-intent-challenge
```

Run without `nano_intent` when no API key is available:

```bash
uv run python -m app.holdout_evaluate retrieval-ablation \
  --questions data/eval/retrieval_intent_challenge.json \
  --strategies raw,deterministic_expansion,rule_intent \
  --run-id retrieval-intent-challenge-local
```

## Evaluation guardrail

The challenge fixture is for this controlled-intent milestone. Do not inspect or tune against the frozen holdout while developing the detector or mapper.
