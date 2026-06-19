# Retrieval Intent Detector Repair

## Scope

This change repairs rule-based intent detection without changing the corpus, chunking, retriever, ranking, or top-K configuration.

## Matching rules

- Short tokens such as `pen` use word-boundary matching.
- Supplier intent requires supplier/manufacturer language plus information-seeking context.
- Manufacturer reporting language does not imply a supplier-information request.
- Administration questions are separated from administration timing context.
- Ingredient composition requests are separated from palatability complaints.
- `device_review` is removed because it is not a canonical workflow concept.
- Every detected full quality review includes trend review, matching the operational workflow.
- Workflow tags are derived from detected evidence rather than chained from one weak keyword.

## Validation

Run the focused checks before the retrieval ablation:

```powershell
uv run python -m pytest tests/test_retrieval_intent.py tests/test_retrieval_query_strategy.py
uv run pyright app/retrieval_intent.py app/retrieval_query_strategy.py tests/test_retrieval_intent.py tests/test_retrieval_query_strategy.py
```

Then rerun the challenge and development comparisons with the same chunks, retriever, top-K, and source labels.
