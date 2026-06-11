# Retrieval Comparison Report

Generated: `2026-06-11T16:47:58Z`
Top K: `5`
Question count: `12`

## Summary

| Retriever | Hit Rate | MRR | Failed IDs | Latency Seconds |
|---|---:|---:|---|---:|
| keyword | 0.833 | 0.750 | RET-007, RET-009 | 0.011371 |
| embedding | 0.917 | 0.812 | RET-007 | 0.019838 |
| hybrid | 0.833 | 0.750 | RET-007, RET-009 | 0.031663 |

## Qualitative Notes

- Best hit_rate@k: embedding.
- Best MRR: embedding.
- Keyword failed questions not failed by embedding: RET-009.
- Embedding failed questions not failed by keyword: None.
- Hybrid failures not present in keyword baseline: None.
- Keyword failures resolved by hybrid: None.

## Interpretation Guardrails

- Keyword retrieval remains the transparent baseline.
- Hashing embeddings are a local deterministic vector baseline, not production semantic search.
- Hybrid retrieval combines normalized keyword and embedding scores; it does not prove quality by itself.
- This report does not claim semantic retrieval superiority.
- Corpus text should not be changed merely to improve retrieval metrics.
