## Spring Boot API Shell

- Added `GET /health`.
- Added `HealthResponse` DTO record.
- Added `HealthControllerTest` with MockMvc.
- Added Swagger/OpenAPI UI.
- Added centralized `ApiErrorResponse` and `GlobalExceptionHandler` with a stable JSON error contract.
- Added mocked `POST /api/checklist` endpoint with request/response DTOs.
- Added validation coverage for blank checklist concern text.
- Added `GlobalExceptionHandlerTest` coverage for invalid request-body validation, malformed JSON bodies, `ResponseStatusException`, and generic fallback errors.
- Preserved incoming `X-Request-Id` on validation failures and generated request IDs when one is not supplied.
- Confirmed `./gradlew clean test` passes from `services/review-api`.

## Python RAG / CLI Update

- Added schema-level `RefusalReason`, `RefusalResult`, and `IntakeUnderstanding` contracts.
- Added optional OpenAI-backed intake-understanding extraction.
- Wired intake understanding into Phase 1 so known concern facts can suppress redundant missing-information items.
- Added semantic boundary detection for unsupported inventory/order, external drug-reference, and clinical/legal conclusion requests.
- Updated reporting tests to avoid brittle exact-copy assertions.
- Confirmed Python tests pass after intake-understanding wiring.

## Python API Runner Bridge

- Added `app/api_runner.py` as the JSON stdin/stdout bridge for the future Java process client.
- Added `checklist` command support using the existing Python checklist engine.
- Added bridge envelope:
  - request: `{"command":"checklist","payload":{"concernText":"..."}}`
  - success: `{"ok":true,"result":{...}}`
  - handled error: `{"ok":false,"error":{"code":"...","message":"..."}}`
- Reserved stdout for machine-readable JSON only.
- Reserved stderr for unexpected tracebacks and diagnostics.
- Added nonzero exit code behavior only for unexpected bridge/engine failures.
- Added `tests/test_api_runner.py` coverage for success, invalid JSON, blank/missing concern text, unknown command, refusal, invalid `topK`, and unexpected engine failure.

## Test Hardening

- Added `tests/test_helpers.py` to normalize expected-output fixtures to current schema enum values during tests.
- Updated evaluation and pipeline tests to treat `app/schemas.py` as the source of truth.
- Updated CLI tests to isolate `cli.main()` from external LLM configuration when LLM behavior is not under test.
- Updated intake-understanding fake client to tolerate the current prompt-call contract.
- Updated reporting assertions to check stable behavior instead of incidental capitalization or exact report prose.
- Updated Spring MVC tests to distinguish controller registration failures from actual exception-handler failures.
- Removed temporary diagnostic assertions from the global exception-handler path after the handler behavior was confirmed.

## Retrieval Closeout

Retrieval comparison work is functionally complete.

The project now includes:

- `KeywordRetriever`
- local deterministic `EmbeddingRetriever`
- `HybridRetriever`
- shared retrieval comparison
- `reports/retrieval_comparison.md`

`KeywordRetriever` remains the default retrieval path for API/checklist behavior.

Embedding and hybrid retrieval are evaluation baselines only. They are not currently promoted as production semantic search and are not the default behavior.

Current retrieval comparison baseline:

| Retriever | hit_rate@5 | MRR | Failed question IDs |
|---|---:|---:|---|
| Keyword | 0.8333 | 0.7500 | `RET-007`, `RET-009` |
| Embedding | 0.9167 | 0.8125 | `RET-007` |
| Hybrid | 0.8333 | 0.7500 | `RET-007`, `RET-009` |

Interpretation:

Embedding outperformed keyword and hybrid on this small synthetic evaluation set, but this does not establish production semantic-search superiority. The embedding implementation remains a deterministic local baseline for comparison. Keyword retrieval remains the default because it is transparent, predictable, and already integrated into the API/checklist path.

Known retrieval misses:

- `RET-007`: low-star customer review with no review text should retrieve SOP-006.
- `RET-009`: temperature-excursion unsupported product-specific stability boundary should retrieve SOP-005/SOP-006.