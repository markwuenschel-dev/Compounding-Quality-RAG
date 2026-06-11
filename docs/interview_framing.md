# Interview Framing

This project is strongest when framed as a domain-specific AI workflow system, not as a generic chatbot.

> I built a local-first synthetic-data RAG assistant for compounding-quality inquiry review. It validates structured outputs with Pydantic, chunks SOP-like guidance with citation metadata, retrieves evidence with authority rules, refuses unsupported requests, supports a two-phase reviewer workflow, and evaluates retrieval and structured-output behavior with a passing pytest suite.

> Swagger/OpenAPI gives consumers a visible API contract. In this project, the Spring Boot layer is becoming the service boundary around the Python RAG engine, so documenting endpoints early helps keep request/response shapes explicit before I add the Python bridge.

## Spring / Backend Talking Points

### Why add Swagger/OpenAPI early?

Swagger/OpenAPI gives consumers a visible API contract. In this project, the Spring Boot layer is becoming the service boundary around the Python RAG engine, so documenting endpoints early helps keep request/response shapes explicit before I add the Python bridge.

### Why put Spring Boot in front of Python?

The Python package already owns the tested RAG behavior: ingestion, retrieval, evaluation, LLM extraction, refusal, and final assessment. Spring Boot adds the enterprise service boundary: HTTP routes, DTO validation, OpenAPI documentation, structured errors, logging, and future authentication/audit controls.

### Why not rewrite the RAG engine in Java?

A rewrite would duplicate tested domain logic and slow down the project. The better engineering choice is to preserve the working Python engine and wrap it behind a stable service contract. Later, the subprocess bridge could be replaced with a FastAPI or HTTP service without changing the public Java API.


### How do validation and error handling work in the Spring API?

The Spring layer rejects malformed or invalid requests at the boundary before the Python engine is involved. `GlobalExceptionHandler` turns validation failures, malformed JSON, explicit response-status exceptions, and unexpected errors into one `ApiErrorResponse` shape with status, message, path, request ID, and field errors when available.

### Why keep a generic fallback handler?

A generic fallback prevents internal implementation details from leaking to API consumers. The logs can preserve diagnostic detail, but the HTTP response should be stable and safe: a `500` status, an `Internal Server Error` reason, and a generic message such as `Unexpected server error`.

### What did the `GlobalExceptionHandlerTest` debugging teach you?

The important lesson was separating framework setup failures from real handler failures. A `404` in the validation test meant the nested test controller was not registered in the WebMvc slice, not that validation was broken. Once the test controller was imported, the request reached validation and the global handler returned the expected `400` shape.

## Python Bridge / Java Integration Talking Points

### What is `api_runner.py`?

`api_runner.py` is a process bridge. It lets a future Java `RagEngineClient` call the Python checklist engine by sending one JSON request through stdin and reading one JSON response from stdout.

### Why use stdin/stdout instead of calling Python logic from Java directly?

It keeps the boundary simple and explicit. Python remains responsible for RAG/checklist behavior. Java remains responsible for the HTTP service contract, validation, OpenAPI, error translation, and orchestration. The bridge can later be replaced by FastAPI or another service without changing the public Spring controller contract.

### Why use an `ok:true` / `ok:false` envelope?

The envelope separates handled engine/application errors from process failures. `ok:false` means Python ran and returned a structured refusal or validation error. A nonzero exit code, timeout, or invalid stdout means the bridge itself failed.

### Why keep stdout JSON-only?

The Java client will parse stdout. If logs or tracebacks are mixed into stdout, the integration becomes brittle. Diagnostics belong on stderr; stdout belongs to the machine-readable response contract.

### How does this map to production design?

The current bridge is a local integration adapter. The production-shaped decision is the separation of concerns: controller → service/client interface → Python adapter. That keeps subprocess details out of the controller and makes the integration replaceable later.

## Retrieval/RAG talking points

### Why keep keyword retrieval as the default if embedding scored higher?

The embedding baseline performed better on the small synthetic retrieval comparison, but I did not promote it to the default path because this project is accuracy- and review-support-oriented. Keyword retrieval is transparent, predictable, and easier to debug when a reviewer asks why evidence was returned.

The embedding and hybrid retrievers are intentionally kept as evaluation baselines. That lets me compare lexical, semantic, and combined retrieval behavior without quietly changing production behavior based on one small eval run.
