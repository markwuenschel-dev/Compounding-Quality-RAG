# Compounding Quality RAG

Synthetic, local-first retrieval and review-support prototype for compounding-quality inquiry review.

> **Status:** Python RAG engine is demo-complete for the deterministic workflow and now has a JSON stdin/stdout bridge consumed by Spring Boot. The Spring Boot `review-api` exposes health, OpenAPI/Swagger, centralized error handling, `POST /api/checklist`, `POST /api/retrieve`, and `POST /api/final-assessment`. Python tests are passing and the Spring app starts successfully against the local Python engine.

## 1. Problem Statement

Technical Services pharmacists review compounding-related quality signals from frontline QRE/general-question submissions and negative customer reviews. These workflows require repeated lookup of guidance, categorization, record-check framing, missing-information identification, escalation screening, and consistent documentation.

**Compounding Quality RAG** surfaces relevant synthetic SOP-like guidance, preserves evidence citations, organizes missing information, refuses unsupported requests, and supports structured human review.

It does **not** make final quality, clinical, legal, customer-resolution, or operational decisions.

## 2. Synthetic Data Boundary

This public repository uses demo-only SOP-like documents, synthetic inquiry examples, and hand-written expected outputs. It does **not** contain real or altered customer, patient, veterinarian, prescription, order, compounding-record, inventory, internal SOP, licensed drug-reference, or proprietary operational data.

Requests asking the tool to inspect real records, consult external drug references, determine clinical causality, make legal conclusions, or decide final resolution are refused or constrained to review-support framing.

## 3. Project Shape

```text
Python RAG engine
  owns ingestion, chunking, retrieval, evaluation, refusal behavior,
  checklist generation, review-summary extraction, and final assessment.

Spring Boot review-api
  owns REST API boundary, DTOs, validation, error handling,
  OpenAPI/Swagger, orchestration, health checks, engine error mapping,
  and future auth/audit.

React/TypeScript review UI
  planned human-in-the-loop review surface.
```

Implemented layers:

| Layer | Status | Notes |
|---|---|---|
| Python RAG engine | Implemented | CLI workflow, retrieval, validation, final assessment, refusal, optional LLM extraction, and `api_runner.py` bridge. |
| Spring Boot API | Implemented backend workflow slice | Health, OpenAPI, error handling, Python bridge client, checklist, retrieve, and final-assessment endpoints. |
| React/TypeScript UI | Planned | Deferred until backend contracts are stable. |
| CI/Docker/runbook | Planned | Future production-shaped hardening. |
| Embeddings/hybrid retrieval | Planned | Deferred until keyword baseline and API workflow are stable. |

## 4. Workflow

```text
Concern text
  -> checklist generation
  -> evidence retrieval
  -> structured reviewer findings
  -> final assessment
```

Checklist output includes concern type, risk lane, review scope, required checks, missing information, escalation triggers to rule out, evidence, and limitations.

`POST /api/retrieve` can retrieve supporting evidence directly without generating a checklist or final assessment.

Final assessment combines concern text and structured reviewer findings. Severe escalation routing depends on structured `severeTriggersObserved`, not raw free-text keyword matching.

## 5. Retrieval Evaluation

Retrieval evaluation compares multiple evidence-retrieval strategies without changing the public evidence contract.

Retrievers:

| Retriever | Purpose | Notes |
|---|---|---|
| `KeywordRetriever` | Transparent lexical baseline | Preserves exact-term evidence lookup and matched terms. |
| `EmbeddingRetriever` | Local vector baseline | Uses deterministic hashing vectors and cosine similarity. This is vector plumbing, not true semantic understanding. |
| `HybridRetriever` | Combined baseline | Combines normalized keyword and vector scores with weighted scoring. |

Evaluation/reporting:

- Labeled retrieval questions define expected source IDs.
- Comparison tracks `hit_rate_at_k`, `mean_reciprocal_rank`, failed question IDs, and latency seconds.
- `reports/retrieval_comparison.md` records keyword, embedding, and hybrid results plus qualitative notes.
- The report is evidence for comparison, not proof that vector or hybrid retrieval is inherently better.

Guardrails:

- Keyword remains the transparent baseline.
- The `SearchResult` shape remains stable: `chunk`, `score`, `matched_terms`.
- No vector database is added yet.
- No corpus edits should be made solely to inflate retrieval metrics.
- The hashing vector baseline should not be described as production semantic search.

## 6. Architecture

```text
HTTP client
  -> Spring controller
  -> Spring application service
  -> RagEngineClient
  -> PythonProcessRagEngineClient
  -> app.api_runner.py
  -> Python workflow logic
```

Spring wraps the Python engine with a production-shaped service boundary without rewriting tested Python logic.

## 7. Repository Structure

```text
app/
  schemas.py
  ingestion.py
  retrieval.py
  retrieval_embedding.py
  retrieval_hybrid.py
  retrieval_compare.py
  retrieval_evaluate.py
  checklist.py
  final_assessment.py
  refusal.py
  review_summary_extraction.py
  reporting.py
  cli.py
  api_runner.py

data/corpus/
data/index/
data/eval/
data/expected_outputs/
reports/
docs/

services/review-api/
  src/main/java/com/compoundingquality/reviewapi/
    api/
    application/
    dto/
    rag/
    config/
    error/
```

## 8. Run Python Locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m app.ingestion
python -m app.retrieval_evaluate
python -m app.retrieval_compare
python -m app.cli
python -m pytest
```

`python -m app.retrieval_compare` writes:

```text
reports/retrieval_comparison.md
```

## 9. Python API Runner Bridge

Checklist:

```powershell
@'
{"command":"checklist","payload":{"concernText":"My dog vomited after taking a flavored compounded oral liquid.","topK":3}}
'@ | python -m app.api_runner
```

Retrieve:

```powershell
@'
{"command":"retrieve","payload":{"queryText":"vomiting after flavored oral liquid","topK":3}}
'@ | python -m app.api_runner
```

Final assessment:

```powershell
@'
{
  "command": "final_assessment",
  "payload": {
    "concernText": "My dog vomited once after taking a chicken-flavored compounded oral liquid and recovered.",
    "topK": 3,
    "reviewSummary": {
      "recordReviewResult": "no_discrepancy_found",
      "lotBatchPatternSummary": "no_similar_batch_concerns_found",
      "inventoryInspectionResult": "no_inventory_available",
      "customerContextSummary": "Dog vomited once and recovered. No hospitalization, death, legal threat, contamination, or wrong medication concern was reported.",
      "apiReferenceReviewResult": "not_needed",
      "missingInformation": ["Exact dose administered"],
      "evidenceLimitations": ["Inventory was not available to inspect."],
      "severeTriggersObserved": []
    }
  }
}
'@ | python -m app.api_runner
```

Bridge rules:

- stdout is JSON only.
- stderr is diagnostics only.
- `ok:false` is a handled application/bridge error.
- nonzero exit code is process/engine failure.

## 10. Run Spring Boot Review API

```powershell
cd services/review-api
.\gradlew clean check
.\gradlew bootRun
```

Swagger/OpenAPI UI:

```text
http://localhost:8080/swagger-ui.html
```

Configuration:

```yaml
rag:
  python:
    command:
      - python
      - -m
      - app.api_runner
    working-directory: ../../rag-engine-python
    timeout: 10s
```

`working-directory` is bound as a string and converted with `Path.of(...)` to avoid Spring resource-path normalization issues.

## 11. API Endpoints

### `GET /health`

Returns service status.

### `POST /api/checklist`

Request:

```json
{"concernText":"My dog vomited after taking a flavored compounded oral liquid.","topK":3}
```

Response includes concern type, risk lane, review scope, checks, missing information, escalation triggers to rule out, evidence, and limitations.

### `POST /api/retrieve`

Request:

```json
{"queryText":"vomiting after flavored oral liquid","topK":3}
```

Response includes evidence citations with `chunkId`, `sourceId`, `sourceTitle`, `sourceType`, `sectionHeading`, `score`, `matchedTerms`, and `supportingText`.

### `POST /api/final-assessment`

Request includes `concernText`, optional `topK`, and structured `reviewSummary`.

Response includes `rawIntake`, `productContext`, `investigationRequirements`, `reviewSummary`, and `derivedAssessment`.

## 12. Manual API Smoke Tests

Retrieve:

```powershell
$retrieveBody = @{
    queryText = "vomiting after flavored oral liquid"
    topK = 3
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://localhost:8080/api/retrieve" `
    -Method Post `
    -ContentType "application/json" `
    -Body $retrieveBody
```

Final assessment:

```powershell
$finalAssessmentBody = @{
    concernText = "My dog vomited once after taking a chicken-flavored compounded oral liquid and recovered."
    topK = 3
    reviewSummary = @{
        recordReviewResult = "no_discrepancy_found"
        lotBatchPatternSummary = "no_similar_batch_concerns_found"
        inventoryInspectionResult = "no_inventory_available"
        customerContextSummary = "Dog vomited once and recovered. No hospitalization, death, legal threat, contamination, or wrong medication concern was reported."
        apiReferenceReviewResult = "not_needed"
        missingInformation = @("Exact dose administered")
        evidenceLimitations = @("Inventory was not available to inspect.")
        severeTriggersObserved = @()
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Uri "http://localhost:8080/api/final-assessment" `
    -Method Post `
    -ContentType "application/json" `
    -Body $finalAssessmentBody
```

Severe trigger routing should return:

```text
riskLane = life_threatening_or_legal
reviewScope = escalation_review
handlingPath = leadership_escalation_before_resolution
```

when `severeTriggersObserved` contains a severe trigger such as `pet_hospitalization`.

## 13. Error Handling

`ApiErrorResponse` fields:

- `timestamp`
- `status`
- `error`
- `message`
- `path`
- `requestId`
- `fieldErrors`
- `code` optional engine code

Mappings:

| Condition | Status |
|---|---:|
| Bean validation failure | 400 |
| Malformed JSON | 400 |
| `INVALID_REQUEST` / `REFUSED` | 422 |
| `ENGINE_TIMEOUT` | 504 |
| `ENGINE_INTERRUPTED` | 503 |
| `ENGINE_REQUEST_ENCODING` | 500 |
| Process/stdout/response/mapping/engine failure | 502 |
| Unexpected Java exception | 500 |

## 14. Design Principles

1. Synthetic-only boundary.
2. Source-grounded evidence.
3. Human-in-the-loop review.
4. Structured severe routing.
5. Java wraps; Python owns RAG.
6. Bridge stdout is machine-only.
7. Explicit contracts over magic.
8. Measure before claiming improvement.
9. Preserve keyword baseline before adding semantic or hybrid retrieval.
10. Report retrieval metrics before making quality claims.

## 15. Next Work

1. Add focused controller/service tests for retrieve and final assessment.
2. Add Python bridge tests for `retrieve` and `final_assessment`.
3. Add one local workflow smoke test.
4. Add API examples/OpenAPI examples.
5. Add React/TypeScript UI.
6. Add CI/Docker/runbook.
7. Replace the hashing vector baseline with a real embedding model only after comparison and operational constraints are clear.
