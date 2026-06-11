# Decisions

## 2026-05-04 — Project boundary

### Decision
Build a source-grounded RAG workbench for synthetic pharmacy/compounding SOP-style documents and synthetic inquiry records.

### Reason
Synthetic documents are safe to publish and let the project control document structure, expected answers, review states, and evaluation cases without exposing proprietary records, internal SOP text, customer information, PHI, PII, or licensed drug-information content.

### Tradeoff
Synthetic documents are safer but less realistic than real operational material.

### Revisit when
A private/internal prototype is approved and read-only integration requirements are known.

---

## 2026-05-04 — Explicit model contracts

### Decision
Use explicit model contracts for source documents, chunks, inquiry records, review summaries, derived assessments, refusals, and bridge payloads.

### Reason
The system needs clear boundaries between source truth, retrieved evidence, reviewer findings, and generated outputs.

### Tradeoff
Schema validation adds overhead, but early failure is valuable in an accuracy-sensitive workflow.

---

## 2026-05-09 — Formal classification versus handling path

### Decision
Separate formal QRE classification from operational handling path.

### Reason
Formal category/subcategory values are documentation concepts. Handling path describes what Technical Services does next.

### Consequence
Synthetic outputs separately represent formal classification, concern type, risk lane, review scope, investigation requirements, handling path, and resolution options.

---

## 2026-05-09 — Risk lane model

### Decision
Use `risk_lane` as a severity and escalation guide separate from formal category and handling path.

### Allowed values
- `expected_self_limiting`
- `unexpected_non_life_threatening`
- `life_threatening_or_legal`

### Reason
The workflow behaves like a risk-tiered investigation.

---

## 2026-05-09 — Frontline pharmacist questions

### Decision
Do not model frontline pharmacist questions as a separate intake source.

### Reason
Frontline questions arrive through the QRE/general-question form. They differ by submitter role, submission purpose, and review scope.

### Canonical representation

```yaml
intake_source: qre_general_question_form
submitter_role: frontline_pharmacist
submission_purpose: frontline_pharmacist_question
review_scope: guidance_only
```

---

## 2026-05-09 — Synthetic review summaries instead of fake system access

### Decision
The public project will not pretend the RAG system has access to compounding records, lot-tracing systems, customer histories, inventory, Snowflake, or external drug-information resources.

### Reason
The public project must be synthetic and safe.

### Consequence
Synthetic records may include `review_summary` as human-entered or synthetic findings. The RAG system can use those summaries, but it must not claim it directly inspected real operational systems.

---

## 2026-05-09 — Resolution options separate from handling path

### Decision
Keep customer-facing resolution options separate from operational handling path.

### Reason
Handling path describes what TS does next. Resolution options describe possible case-closure/customer-facing actions.

---

## 2026-05-18 — Structured severe escalation triggers

### Decision
Use `review_summary.severe_triggers_observed` as the structured source of truth for severe escalation routing.

### Reason
Free text can contain negated severe terms such as “no hospitalization” or “no wrong medication concern.” Keyword scanning can misread them as positive escalation evidence.

### Consequence
Final routing escalates to `life_threatening_or_legal` only when structured severe triggers are supplied.

---

## 2026-05-30 — Python process bridge contract

### Decision
Add `app/api_runner.py` as a JSON stdin/stdout process bridge between Spring Boot and the Python engine.

### Reason
Python owns the tested RAG behavior. Java/Spring should wrap it rather than rewrite it.

### Contract

```json
{"command":"checklist","payload":{"concernText":"...","topK":5}}
```

Success:

```json
{"ok":true,"result":{}}
```

Handled error:

```json
{"ok":false,"error":{"code":"REFUSED","message":"..."}}
```

### Consequence
stdout is machine-readable JSON only. stderr is diagnostics only.

---

## 2026-05-31 — Java `RagEngineClient` interface

### Decision
Hide the Python subprocess implementation behind a Java `RagEngineClient` interface.

### Reason
Controllers and services should depend on a stable domain-facing client, not process-management details.

### Current methods

```java
RagChecklistResult createChecklist(RagChecklistRequest request);
RagRetrieveResult retrieve(RagRetrieveRequest request);
RagFinalAssessmentResult createFinalAssessment(RagFinalAssessmentRequest request);
```

### Revisit when
The subprocess bridge is replaced by FastAPI or another deployable Python service.

---

## 2026-06-05 — Backend workflow endpoint expansion

### Decision
Add Spring endpoints for retrieval and final assessment instead of stopping at checklist generation.

### Reason
Checklist-only integration proved the bridge worked, but did not demonstrate the full review workflow. Retrieval and final assessment create a realistic backend slice.

### Endpoints
- `POST /api/checklist`
- `POST /api/retrieve`
- `POST /api/final-assessment`

### Consequence
The Java/Spring service now exercises multiple Python bridge commands and maps nested structures across the process boundary.

---

## 2026-06-05 — Spring owns HTTP; Python owns RAG/domain behavior

### Decision
Keep domain routing, retrieval, refusal, checklist, and final-assessment logic in Python. Keep HTTP routes, DTO validation, structured errors, OpenAPI, configuration, and orchestration in Spring.

### Architecture

```text
HTTP client
  -> Spring controller
  -> Spring application service
  -> RagEngineClient
  -> PythonProcessRagEngineClient
  -> app.api_runner.py
  -> Python workflow logic
```

### Tradeoff
Local development must configure both Java and Python correctly, and failures can occur at the serialization/process boundary.

---

## 2026-06-05 — Jackson 3 alignment for Spring Boot 4

### Decision
Use Jackson 3 `tools.jackson.databind.json.JsonMapper` consistently at the Spring/Python bridge boundary.

### Reason
Spring Boot 4 defaults to the Jackson 3 stack. Mixing Jackson 2 `ObjectMapper` and Jackson 3 `JsonMapper` caused application-context and test-context mismatch.

### Consequence
The bridge/config boundary and related tests now use Jackson 3 consistently.

---

## 2026-06-05 — Bind `rag.python.working-directory` as string

### Decision
Bind `rag.python.working-directory` as a string and convert it with `Path.of(...)` at the client-properties boundary.

### Reason
Direct Spring binding to `Path` treated `../../rag-engine-python` as a resource-style path and rejected it after normalization.

### Consequence
The YAML can keep a relative local path while the app starts successfully.

---

## 2026-06-05 — Engine errors mapped explicitly to HTTP statuses

### Decision
Map `RagEngineException` to structured HTTP responses instead of letting downstream bridge failures fall through generic 500 handling.

### Mapping
- `INVALID_REQUEST`, `REFUSED` -> 422.
- `ENGINE_TIMEOUT` -> 504.
- `ENGINE_INTERRUPTED` -> 503.
- `ENGINE_REQUEST_ENCODING` -> 500.
- process/stdout/response/mapping/engine failures -> 502.

### Consequence
`ApiErrorResponse` has optional `code` for engine errors.

---

## 2026-06-09 — Preserve keyword retrieval as baseline

### Decision
Keep keyword retrieval as the transparent baseline behind `KeywordRetriever`.

### Reason
Keyword retrieval is interpretable, auditable, and useful for exact SOP/process terms. It provides a stable comparison point before adding vector or hybrid retrieval.

### Consequence
New retrieval strategies must be compared against keyword rather than replacing it silently.

---

## 2026-06-09 — Add local deterministic vector baseline before production semantic search

### Decision
Add a local deterministic hashing-vector `EmbeddingRetriever` before introducing external embedding models or a vector database.

### Reason
The project needs testable vector retrieval plumbing and comparison infrastructure before adding model downloads, external APIs, persistence, or infrastructure.

### Tradeoff
The hashing-vector model is not true semantic search. It does not understand synonyms such as `emesis` and `vomiting` unless lexical overlap or hash collision creates similarity.

### Consequence
The current vector baseline must be described as local vector retrieval plumbing, not production semantic retrieval.

---

## 2026-06-09 — Add hybrid retrieval with normalized component scores

### Decision
Add `HybridRetriever` that combines normalized keyword and vector scores with configurable weights.

### Reason
Keyword and cosine-similarity scores are on different scales. Normalization is required before weighted combination.

### Default weights
- keyword: `0.65`
- vector: `0.35`

### Consequence
Hybrid retrieval can be evaluated alongside keyword and vector retrieval without changing the public `SearchResult` contract.

---

## 2026-06-09 — Generate retrieval comparison report before quality claims

### Decision
Generate `reports/retrieval_comparison.md` comparing keyword, vector, and hybrid retrieval.

### Report fields
- hit_rate@k
- mean reciprocal rank
- failed question IDs
- latency seconds
- qualitative notes
- interpretation guardrails

### Reason
Retrieval quality should be measured before claiming improvement.

### Consequence
The project can discuss retrieval tradeoffs using evidence from the synthetic evaluation set while avoiding unsupported claims that vector or hybrid retrieval is generally superior.

---

## 2026-06-09 — Defer vector database and persisted vector store

### Decision
Do not add a vector database or persisted vector store during the local retrieval baseline.

### Reason
The corpus is small and the current hashing-vector model is not the final semantic model. Persisting this index would add infrastructure before it proves value.

### Revisit when
A real embedding model is added, corpus size grows, retrieval latency becomes a measurable problem, or deployment requires persistent precomputed vectors.
