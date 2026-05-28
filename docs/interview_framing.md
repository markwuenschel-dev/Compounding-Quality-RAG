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
## Intake Understanding / LLM Boundary Talking Points

### Why add an intake-understanding layer?

The first version of the checklist could identify concern types, but it sometimes asked for facts already supplied in the concern text. I added a schema-validated `IntakeUnderstanding` layer so the system can capture product context, customer context, facts present, facts missing, and possible boundary issues before checklist generation.

### Why not let the LLM generate the checklist?

The LLM is treated as a structured extraction dependency, not a decision engine. It extracts facts into a Pydantic model. Deterministic application code still owns refusal handling, checklist generation, escalation routing, and final assessment.

### What makes this safer than a chatbot?

The workflow has explicit boundaries: deterministic refusal runs first, optional semantic boundary detection can stop unsupported requests, structured reviewer findings drive final escalation, and the reports repeat that the project uses synthetic data only.
