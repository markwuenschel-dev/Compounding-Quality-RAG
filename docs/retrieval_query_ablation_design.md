# Retrieval Query Ablation

## Purpose

This experiment measures whether query interpretation improves retrieval while holding the rest of the retrieval system constant.

The compared strategies are:

1. `raw`
2. `deterministic_expansion`
3. `nano_structured`

The corpus, chunks, keyword retriever, `top_k`, development questions, expected sources, forbidden sources, and scoring functions are unchanged.

## Architecture

```text
development question
        |
        v
query strategy
        |
        v
RetrievalQueryIntent.search_text
        |
        v
existing keyword retriever
        |
        v
existing holdout-style scoring
```

The retriever still receives one string. The experiment changes only how that string is built.

## Why this is separate from `retrieval_compare.py`

`retrieval_compare.py` compares retriever implementations:

- keyword
- local hashing embedding
- hybrid

This ablation compares query-building strategies while using the same retriever. Combining both questions in one comparison would make the result hard to interpret.

## Strategy definitions

### Raw

Uses the original complaint unchanged.

This is the control.

### Deterministic expansion

Keeps the original complaint and appends controlled retrieval concepts for observed failure classes:

- hospitalization and gastrointestinal adverse events;
- neurologic signs;
- respiratory context;
- inactive-ingredient and proprietary-formula questions;
- supplier/manufacturer disclosure;
- BUD and stability boundaries;
- dispensing-device concerns;
- therapeutic-response concerns.

### Nano structured

Calls the configured OpenAI JSON client and asks for:

- a concise retrieval-oriented phrase;
- issue tags;
- required policy topics;
- excluded topics.

The original complaint is retained and the generated concepts are appended. The returned object is validated with Pydantic.

If the model returns malformed structured output, the strategy records a fallback and uses deterministic expansion for that question. Provider errors still fail the run rather than silently creating a fake nano comparison.

## Nano cache

Nano intents are stored in:

```text
rag-engine-python/artifacts/runs/<run-id>/nano_intents.jsonl
```

The key contains:

- question ID;
- SHA-256 of the complaint text;
- model name.

A second run with the same run ID reuses the cached, validated intent. Use `--refresh-nano` to call the model again.

## Metrics

Each strategy records:

- hit rate at K;
- mean reciprocal rank;
- negative-constraint pass rate;
- failed question IDs;
- forbidden-hit question IDs;
- query-build latency;
- retrieval latency;
- total latency;
- model calls;
- nano cache hits and misses;
- fallback count;
- structured-output failures;
- provider errors.

Question-level output records the original query, actual search text, tags, topics, retrieved sources, rank, forbidden hits, and fallback status.

## Artifacts

A run writes:

```text
rag-engine-python/artifacts/runs/<run-id>/
├── run_manifest.json
├── raw_results.json
├── deterministic_expansion_results.json
├── nano_structured_results.json
├── nano_intents.jsonl
├── comparison.json
└── comparison.md
```

The directory is ignored by Git except for its `.gitignore`.

## Development-label correction

Two development questions previously treated shortness of breath or collapse-like context as escalation-oriented retrieval.

Confirmed policy is:

- hospitalization remains a severe escalation topic;
- shortness of breath alone is clinical context and favors outreach;
- collapse or falling over alone is clinical context;
- both still require adverse-event guidance.

Therefore `DEV-RET-014-PAIR-0157` and `DEV-RET-020-PAIR-0304` now expect `SOP-005`, not `SOP-007`.

## Run

From `rag-engine-python`:

```powershell
python -m app.holdout_evaluate retrieval-ablation `
  --questions data/eval/retrieval_questions_development.json `
  --strategies raw,deterministic_expansion,nano_structured `
  --top-k 5 `
  --run-id retrieval-dev-ablation
```

The configured model comes from `OPENAI_MODEL`, defaulting through the existing client to `gpt-5-nano`.

To replay the cached nano intents, run the same command again.

To call nano again:

```powershell
python -m app.holdout_evaluate retrieval-ablation `
  --questions data/eval/retrieval_questions_development.json `
  --strategies raw,deterministic_expansion,nano_structured `
  --top-k 5 `
  --run-id retrieval-dev-ablation `
  --refresh-nano
```

## How to interpret the experiment

- Raw miss, deterministic hit, nano hit: semantic expansion helps; an LLM may not be necessary.
- Raw miss, deterministic miss, nano hit: measurable marginal value from nano.
- All three miss: likely corpus wording, chunking, or scoring rather than query interpretation.
- Nano creates forbidden hits: the model expansion is too broad.
- Deterministic nearly matches nano: use rules by default and reserve nano for difficult cases.
- Nano clearly wins: consider nano normalization with deterministic fallback.

## Interview framing

> I held the corpus, chunks, retriever, labels, and scoring constant and changed only query construction. Raw text, deterministic expansion, and nano-generated structured intent all implemented the same typed interface. Nano results were cached by input hash and model for reproducibility, and unit tests used stubs rather than live API calls. That let me measure the model's marginal retrieval value instead of assuming an LLM call improved the system.
