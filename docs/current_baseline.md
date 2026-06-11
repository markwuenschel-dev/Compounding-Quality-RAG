# Current Baseline

## Snapshot

The project has moved from a Python-only CLI proof of concept into a Spring-wrapped backend workflow prototype with implemented retrieval-evaluation baselines.

Current verified state:

- Public data boundary: synthetic/demo-only.
- Spring Boot `review-api`: application loads successfully with the local Python engine configuration.
- Implemented HTTP endpoints:
  - `GET /health`
  - `POST /api/checklist`
  - `POST /api/retrieve`
  - `POST /api/final-assessment`
- Python retrieval now has:
  - `Retriever` protocol.
  - `KeywordRetriever` baseline.
  - local deterministic `EmbeddingRetriever` baseline.
  - `HybridRetriever` baseline.
  - retrieval-comparison scaffold.
  - generated comparison report at `rag-engine-python/reports/retrieval_comparison.md`.
- Keyword retrieval remains the default bridge/checklist retrieval path.
- Embedding and hybrid retrieval are comparison baselines, not production semantic search modes.

## Implemented Python Engine Capabilities

- Synthetic SOP schema and corpus.
- Pydantic model validation.
- SOP ingestion and chunking.
- Keyword retrieval baseline with evidence metadata and matched terms.
- `Retriever` protocol and `KeywordRetriever` implementation.
- Retrieval evaluation with hit-rate@k and MRR-style metrics.
- Retrieval comparison scaffold for side-by-side retriever metrics, failed IDs, latency, and qualitative notes.
- Local deterministic `HashingEmbeddingModel` and `EmbeddingRetriever` baseline.
- `HybridRetriever` combining normalized keyword and vector scores.
- Generated retrieval comparison report at `reports/retrieval_comparison.md`.
- Refusal detection for unsupported internal-record access, external drug-reference requests, and clinical/legal conclusion requests.
- Phase 1 checklist generation.
- Optional intake-understanding extraction.
- Optional OpenAI-backed review-summary extraction.
- Phase 2 final-assessment generation.
- Structured severe-trigger routing through `review_summary.severe_triggers_observed`.
- Two-phase CLI workflow.
- JSON stdin/stdout process bridge in `app/api_runner.py`.

## Implemented Spring Boot Capabilities

- Spring Boot `review-api` service.
- Swagger/OpenAPI UI.
- Centralized `ApiErrorResponse` contract.
- `GlobalExceptionHandler` with request IDs, validation field errors, and engine error codes.
- `RagEngineClient` interface.
- `PythonProcessRagEngineClient` subprocess adapter.
- Jackson 3 `JsonMapper` boundary for Spring Boot 4.
- Python process timeout, exit-code, stdout, handled-error, and mapping-failure handling.
- Working-directory configuration bound as string and converted with `Path.of(...)`.
- `POST /api/checklist` backed by the Python bridge.
- `POST /api/retrieve` backed by the Python bridge.
- `POST /api/final-assessment` backed by the Python bridge.

## Current Retrieval Evaluation

| Retriever | Status | Notes |
|---|---|---|
| Keyword | Default baseline | Transparent lexical retrieval, matched terms, deterministic ordering. |
| Local embedding | Evaluation baseline | Hashing-vector model with cosine similarity. Useful for vector plumbing and comparison, not true semantic understanding. |
| Hybrid | Evaluation baseline | Combines normalized keyword and vector scores with weighted scoring. |
| Real semantic embedding | Planned | Should be added behind `EmbeddingModel` after the local comparison path is stable. |

The comparison report is generated with:

```powershell
cd rag-engine-python
python -m app.retrieval_compare
```

Report artifact:

```text
rag-engine-python/reports/retrieval_comparison.md
```

Current comparison metrics:

- `hit_rate_at_k`
- `mean_reciprocal_rank`
- failed question IDs
- latency seconds
- qualitative notes
- interpretation guardrails

Important metric boundaries:

- `hit_rate@k` answers whether at least one expected source appeared in the top-k results.
- MRR measures how early the first expected source appeared.
- `SearchResult.score` is retriever-specific and should not be compared directly across retrieval strategies.
- Hybrid retrieval normalizes keyword and vector component scores before weighting.
- The local hashing embedding model does not know synonyms such as `emesis` and `vomiting` unless lexical overlap or hash collisions create similarity.
- The comparison report measures behavior on the synthetic evaluation set; it does not prove production semantic retrieval quality.

## Current Python Bridge Commands

| Command | Purpose |
|---|---|
| `checklist` | Generate Phase 1 intake checklist from concern text. |
| `retrieve` | Retrieve SOP evidence for a query. |
| `final_assessment` | Generate Phase 2 final assessment from concern text and structured reviewer findings. |

Bridge rules:

- Request envelope: `{"command":"...","payload":{...}}`.
- Success envelope: `{"ok":true,"result":{...}}`.
- Handled error envelope: `{"ok":false,"error":{"code":"...","message":"...","details":{...}}}`.
- stdout must contain one JSON response only.
- stderr is reserved for diagnostics and tracebacks.
- `ok:false` is a handled application/bridge error.
- Nonzero exit code is a process-level failure.

## Current REST Endpoints

### `GET /health`

Returns service status.

### `POST /api/checklist`

Generates Phase 1 output: concern type, risk lane, review scope, initial takeaway, required checks, missing information, escalation triggers to rule out, evidence, and limitations.

### `POST /api/retrieve`

Returns query text, topK, and retrieved evidence citations with chunk ID, source ID, title, source type, section heading, score, matched terms, and supporting text.

### `POST /api/final-assessment`

Accepts concern text, topK, and structured reviewer findings. Returns raw intake, product context, investigation requirements, supplied review summary, and derived assessment.

## Current Error Handling

| Condition | HTTP status |
|---|---:|
| Bean validation failure | 400 |
| Malformed JSON | 400 |
| `INVALID_REQUEST` from Python | 422 |
| `REFUSED` from Python | 422 |
| `ENGINE_TIMEOUT` | 504 |
| `ENGINE_INTERRUPTED` | 503 |
| `ENGINE_REQUEST_ENCODING` | 500 |
| Process/stdout/response/mapping/engine failures | 502 |
| Unexpected Java exception | 500 |

## Recent Fixes / Additions

- Restored `@Bean` on `RagEngineConfiguration.ragEngineClient(...)`.
- Expanded `RagEngineClient` and `PythonProcessRagEngineClient` consistently for `retrieve(...)` and `createFinalAssessment(...)`.
- Migrated the bridge/config boundary to Jackson 3.
- Fixed Jackson test assertions to compare scalar values, not `JsonNode` objects.
- Replaced deprecated `HttpStatus.UNPROCESSABLE_ENTITY` with `UNPROCESSABLE_CONTENT`.
- Changed `rag.python.working-directory` binding from `Path` to `String`, then explicitly converted with `Path.of(...)`.
- Added retriever abstraction and keyword baseline wrapper.
- Added retrieval comparison scaffold.
- Added local deterministic embedding retriever baseline.
- Added hybrid retriever with normalized keyword/vector scoring.
- Added retrieval comparison report artifact.

## Current Limitations

- No React/TypeScript UI yet.
- No Docker Compose/runbook yet.
- No persistence/audit database yet.
- No real semantic embedding model yet.
- No vector database or persisted embedding index yet.
- No LLM-backed review-summary extraction REST endpoint yet.
- No authentication, authorization, or audit trail yet.
- Public project remains synthetic-only.

## Next Recommended Work

1. Add React/TypeScript UI for the review workflow.
2. Add CI/Docker/runbook.
3. Add persistence/audit design.
4. Replace the hashing-vector baseline with a real embedding model behind `EmbeddingModel` after comparison constraints are clear.
5. Add persisted embedding/index metadata and invalidation rules before considering a vector database.
6. Add focused tests for `RetrieveService`, `FinalAssessmentService`, `RetrieveController`, and `FinalAssessmentController`.
7. Add Python bridge tests for `retrieve` and `final_assessment`.
8. Add one local workflow smoke test covering Spring -> Python -> final assessment.
9. Add REST examples/OpenAPI examples for the current endpoints.
