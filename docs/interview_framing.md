# Interview Framing

This project is strongest when framed as a **domain-specific AI workflow system**, not as a generic chatbot.

## Core Pitch

> I built a local-first synthetic-data RAG assistant for compounding-quality inquiry review. It validates structured outputs with Pydantic, chunks SOP-like guidance with citation metadata, retrieves evidence with authority rules, refuses unsupported requests, supports a two-step reviewer workflow, and evaluates retrieval and structured-output behavior with a passing Python test suite.

Updated backend pitch:

> I wrapped the tested Python RAG engine with a Spring Boot API boundary. Spring owns HTTP routes, DTO validation, OpenAPI visibility, structured error responses, and a replaceable `RagEngineClient` interface, while Python owns retrieval, refusal behavior, checklist generation, and final-assessment logic.

Updated retrieval evaluation pitch:

> I preserved keyword retrieval as a transparent baseline, introduced a shared retriever abstraction, added local deterministic vector retrieval, implemented hybrid retrieval with normalized keyword/vector scoring, and generated a comparison report using hit_rate@k, MRR, failed IDs, latency, and qualitative notes. I treated vector retrieval as something to measure, not something to assume was better.

## What to Call the Project

| Audience | Framing |
|---|---|
| MLE / AI | Source-grounded AI workflow system with measured retrieval baselines for synthetic pharmacy-quality review. |
| SWE / Internal tools | Production-shaped internal AI application with Spring Boot API and Python engine integration. |
| Data / BI | Evidence-organizing workflow assistant with explicit contracts, evaluation, and audit-friendly outputs. |
| Pharmacy leadership | Review-support prototype that organizes evidence and missing information without replacing pharmacist judgment. |

Avoid calling it just a chatbot.

## Architecture Walkthrough

```text
Synthetic SOP corpus
  -> ingestion/chunking
  -> retrieval evidence
  -> checklist generation
  -> structured reviewer findings
  -> final assessment
  -> Spring Boot API boundary
```

Service boundary:

```text
HTTP client
  -> Spring controller
  -> application service
  -> RagEngineClient interface
  -> PythonProcessRagEngineClient subprocess adapter
  -> app.api_runner.py
  -> Python RAG/domain logic
```

Retrieval evaluation boundary:

```text
Retrieval questions
  -> KeywordRetriever
  -> EmbeddingRetriever
  -> HybridRetriever
  -> shared evaluator
  -> retrieval_comparison.md
```

## Spring / Backend Talking Points

### Why put Spring Boot in front of Python?

The Python package already owns the tested RAG behavior: ingestion, retrieval, evaluation, LLM extraction, refusal, checklist generation, and final assessment. Spring Boot adds the enterprise service boundary: HTTP routes, DTO validation, OpenAPI documentation, structured errors, configuration, health checks, and future authentication/audit controls.

### Why not rewrite the RAG engine in Java?

A rewrite would duplicate tested domain logic and slow down the project. The better engineering choice is to preserve the working Python engine and wrap it behind a stable service contract. Later, the subprocess bridge could be replaced with FastAPI without changing the public Spring controller contract.

### Controller vs service vs client adapter

- **Controller:** HTTP route, request binding, validation trigger, response status.
- **Service:** Use-case orchestration and DTO/RAG record mapping.
- **Client adapter:** Python process execution, bridge JSON, timeout handling, stdout/stderr parsing, engine exception classification.
- **Python engine:** Retrieval, refusal, checklist, final assessment, schema validation.

### Why use `RagEngineClient` as an interface?

It hides the integration mechanism. Today the implementation is a subprocess bridge. Later it could be an HTTP client, message queue, local mock, or test fake without changing controllers.

### Error handling

- Bad request shape or Bean Validation failure: `400`.
- Handled engine invalid request/refusal: `422`.
- Python timeout: `504`.
- Interrupted engine call: `503`.
- Python process, stdout, response, or mapping failure: `502`.
- Java request encoding failure: `500`.
- Unexpected Java exception: `500`.

### Debugging lessons from the Spring integration

- Missing `@Bean` meant no `RagEngineClient` existed.
- Mixing Jackson 2 and Jackson 3 broke Spring Boot 4 runtime wiring.
- Binding `../../rag-engine-python` directly to `Path` failed; binding as `String` and converting with `Path.of(...)` fixed it.
- Comparing `JsonNode` directly to a string made a test fail even though the JSON content was correct.
- Interface/implementation drift was caught at compile time when `RagEngineClient` expanded.

## Python Bridge Talking Points

### What is `api_runner.py`?

`api_runner.py` is a process bridge. Java sends one JSON request through stdin and reads one JSON response from stdout.

### Why stdin/stdout?

It keeps the boundary simple and explicit. Python remains responsible for RAG behavior. Java remains responsible for HTTP contracts and operational semantics.

### Why an `ok:true` / `ok:false` envelope?

```text
ok:false
  Python ran and returned a structured refusal or validation error.

nonzero exit / timeout / invalid stdout
  The bridge/process boundary failed.
```

### Why stdout JSON-only?

The Java client parses stdout. Logs or tracebacks on stdout break the integration. Diagnostics belong on stderr.

## RAG / MLE Talking Points

### Why keyword retrieval before vector retrieval?

Keyword retrieval is transparent and measurable. It gives a baseline for hit rate, MRR, matched terms, and failure analysis. Vector retrieval should be added after the baseline is understood.

### Why add a retriever abstraction?

A shared `Retriever.search(...)` contract lets keyword, local vector, and hybrid retrieval return the same `SearchResult` shape. That keeps checklist generation, evidence citations, and evaluation code from depending on one retrieval implementation.

### What does the local vector baseline prove?

It proves the vector retrieval plumbing:

- chunk text can be converted into fixed-length vectors;
- query text can be converted the same way;
- cosine similarity can rank chunks;
- vector results can preserve the `SearchResult` contract;
- keyword, vector, and hybrid retrievers can be compared through the same evaluator.

It does not prove production semantic understanding.

### Why not call the current vector model semantic search?

The current `HashingEmbeddingModel` is deterministic and local. It behaves like hashed bag-of-words vectors. It does not know that `emesis` means `vomiting` unless a real semantic model is added or lexical/hash overlap happens accidentally.

### Why hybrid retrieval?

Keyword retrieval is strong for exact process terms, SOP language, and auditable matched terms. Local vector retrieval can test whether cosine-similarity ranking adds retrieval coverage. Hybrid retrieval combines normalized keyword and vector scores so the system can preserve lexical precision while measuring whether vector similarity adds value.

### Why normalize hybrid scores?

Keyword scores and cosine similarity are not on the same scale. Directly adding them would let one scoring system dominate for mathematical reasons rather than retrieval quality reasons. Hybrid scoring normalizes each component before applying weights.

### Why not add a vector database yet?

The corpus is small. Brute-force local vector comparison is enough to validate behavior. A vector database would add infrastructure before the retrieval strategy proves it needs one.

### How do you evaluate retrieval?

Use labeled retrieval questions with expected source IDs. Track whether the correct source appears in top-k and how early it appears. Record misses and compare failed IDs between retrievers.

Important metric distinctions:

- `hit_rate@k` asks whether at least one expected source appeared in top-k.
- MRR asks how early the first expected source appeared.
- Hit-rate is not recall.
- Raw scores are retriever-specific and should not be compared directly across keyword, vector, and hybrid retrieval.

### What does the retrieval comparison report prove?

It proves that retrievers can be evaluated through the same contract and compared using stable metrics. It does not prove that semantic retrieval is production-ready. The report is evidence for where keyword, local vector, or hybrid retrieval helped or failed on the synthetic evaluation set.

### Why synthetic SOPs?

Synthetic SOPs demonstrate workflow shape without exposing proprietary SOPs, real customer data, patient data, order records, or licensed drug-reference content.

### How do you prevent unsupported claims?

The system has explicit refusal boundaries for internal-record access, external drug-reference requests, and clinical/legal conclusions. Final assessment is review support, not a final clinical/legal/customer-resolution decision.

### Why structured severe triggers?

Free text can contain negated severe terms like “no hospitalization.” Structured `severeTriggersObserved` prevents false escalation and makes final risk lane auditable.

## Debugging Story Bank

### Jackson 2 / Jackson 3 mismatch

**Situation:** Spring Boot 4 app failed to start because no Jackson 2 `ObjectMapper` bean existed.

**Diagnosis:** Tests registered Jackson 3 `JsonMapper`, but production config still requested Jackson 2.

**Fix:** Migrated the RAG bridge/config boundary consistently to Jackson 3.

### Working directory binding failure

**Situation:** App failed to bind `rag.python.working-directory` to `Path` for `../../rag-engine-python`.

**Diagnosis:** Spring treated the value as a resource-style path.

**Fix:** Bound as `String` and converted explicitly with `Path.of(...)`.

### Interface/implementation drift

**Situation:** Compile failed because `PythonProcessRagEngineClient` did not implement new `RagEngineClient` methods.

**Diagnosis:** The interface moved ahead of the implementation.

**Fix:** Replaced both files with matching signatures.

### Response mapping failure wrapped by Jackson

**Situation:** A test expected `IllegalArgumentException` directly, but Jackson wrapped it during record construction.

**Diagnosis:** The public failure was still `ENGINE_RESPONSE_MAPPING`; the wrapper was implementation detail.

**Fix:** Assert public error code and root cause.

### Retrieval metric misunderstanding

**Situation:** A test treated hit-rate like recall and expected partial credit when one of two expected source IDs was found.

**Diagnosis:** The evaluator defines hit-rate per question: any expected source in top-k is a hit.

**Fix:** Assert metric definitions directly and document hit-rate vs MRR vs recall.

### Local vector synonym misunderstanding

**Situation:** A test expected a local hashing-vector model to retrieve `vomiting` for a query containing `emesis`.

**Diagnosis:** The baseline was vector plumbing, not real semantic search.

**Fix:** Keep the limitation explicit and add real semantic embeddings later behind the same protocol.

### Hybrid scoring/ranking issue

**Situation:** Hybrid retrieval initially scored only the first eligible candidate because the candidate-scoring return was indented inside the loop.

**Diagnosis:** Ranking requires collecting all candidates, normalizing component scores across the full candidate set, then sorting.

**Fix:** Move scoring return outside the loop and add tests where the best candidate is not first in input order.

## Resume / PR Language

> Built a Spring Boot API boundary around a Python RAG engine using a typed `RagEngineClient`, subprocess JSON bridge, DTO validation, centralized error handling, and endpoints for checklist generation, evidence retrieval, and final assessment.

> Designed a replaceable Java/Python integration boundary where Spring owns HTTP contracts and operational error semantics while Python owns tested retrieval and domain workflow logic.

> Added keyword, local vector, and hybrid retrieval baselines behind a shared retriever contract, then generated a retrieval comparison report with hit_rate@k, MRR, failed IDs, latency, and qualitative guardrails.

> Diagnosed and fixed cross-language integration failures involving Jackson 3 migration, Spring configuration binding, process stdout protocol discipline, and typed response mapping.

## Five-Minute Demo Script

1. State the synthetic boundary.
2. Show `POST /api/retrieve` returning evidence with citations.
3. Show `POST /api/final-assessment` with structured reviewer findings.
4. Point out that negated severe language does not escalate.
5. Show explicit severe trigger causing escalation.
6. Show refusal for real record access.
7. Show `reports/retrieval_comparison.md` comparing keyword, local vector, and hybrid retrieval.
8. Close with architecture: Spring owns service boundary; Python owns RAG behavior and retrieval evaluation.
