# Interview Framing

Updated: 2026-06-25

This project is strongest when framed as a domain-specific AI workflow system, not as a generic chatbot.

> I built a local-first, synthetic-data AI review workbench for compounding-quality workflows. React provides the human-review interface, Spring Boot owns the enterprise API boundary and runtime orchestration, and Python FastAPI owns retrieval, structured extraction, deterministic policy grounding, evaluation, refusal behavior, and final assessment.

## Core architecture answer

### Why this architecture?

Python already contained the tested RAG and domain-evaluation engine. Spring Boot provides an enterprise-shaped service boundary with HTTP routes, DTO validation, OpenAPI, structured errors, readiness checks, request correlation, and a future path to authentication and audit. React provides a human-review interface instead of pretending the model should make an autonomous decision.

Current boundary:

```text
React UI -> Spring Boot review-api -> Python FastAPI rag-engine
```

All three services run locally under Docker Compose with health-gated startup.

### Why not rewrite Python logic in Java?

A rewrite would duplicate tested behavior and create migration risk. The better engineering choice was to preserve the working Python domain engine behind a stable Java contract.

The boundary started as stdin/stdout and was replaced by an HTTP FastAPI service. The runtime boundary became more production-shaped without rewriting domain behavior.

## Retrieval answer

Current runtime accuracy path:

```text
Nano semantic intent -> deterministic workflow derivation -> shared vocabulary mapper -> keyword retrieval
```

Fallback path:

```text
Rule semantic intent -> deterministic workflow derivation -> shared vocabulary mapper -> keyword retrieval
```

Frozen holdout result:

| Strategy | Hit rate@5 | MRR | Negative pass |
|---|---:|---:|---:|
| Raw | 0.700 | 0.567 | 0.850 |
| Deterministic expansion | 0.850 | 0.733 | 0.850 |
| Rule intent | 0.750 | 0.725 | 0.900 |
| Nano intent | 0.950 | 0.950 | 1.000 |

Phrase it honestly:

> Nano intent was the strongest measured generalization path on the frozen synthetic holdout, but it has latency, cost, and dependency tradeoffs. Rule intent remains fallback. I closed retrieval experimentation for the current product milestone and moved to operational hardening.

## Review-summary extraction answer

Pipeline:

```text
LLM candidate -> Pydantic validation -> deterministic grounding -> review-scope defaults -> unresolved questions -> evidence mapping -> evaluation
```

The LLM handles language variation. Deterministic code handles workflow-critical semantics such as negation, same-lot patterns, completed versus needed references, non-disclosure, missing investigation steps, device-failure context, administered-dose context, and severe triggers.

### Why not LLM-only?

Because an LLM-only system was inconsistent about omitted fields and overlapping phrases:

- `No external reference needed` contains `external reference needed`.
- `15 mg/mL, 30 mL` is strength/package size, not administered dose.
- `Worksheet review found no discrepancy` is completed record review.
- `One additional quality complaint was identified for the lot` must normalize to a controlled lot-pattern value.
- Coordinated negation lists must not create severe triggers.

## Observability and operations answer

Operational pieces now present:

- Docker Compose local stack;
- health-gated startup;
- Spring `/health` and `/ready`;
- Python `/health`;
- structured Spring error responses;
- request correlation with `X-Request-Id`;
- operations runbook;
- Python smoke script for request correlation.

Request correlation explanation:

> Spring accepts or generates `X-Request-Id`, puts it in MDC, echoes it in the response, and forwards it to Python. Python reads, echoes, and logs it. That lets me connect a UI/API request to Spring logs and Python logs.

## Strong debugging story

> I started with extraction failures that looked like model mistakes, but instead of prompt-tuning blindly I grouped errors by mechanism. I found negation precedence, review-scope silence, broad substring matching, administered-dose confusion, incomplete reference states, and unnormalized lot language. I fixed each mechanism in deterministic code, wrote a regression test that reproduced it, and reran the benchmark.

## Strong architecture migration story

> The first Spring-to-Python boundary used a subprocess runner. That proved the workflow but coupled Spring to Python interpreter discovery, working directory, and stdout/stderr parsing. I replaced it with a FastAPI service and HTTP client, then ran React, Spring, and Python under Docker Compose. That gave each service its own lifecycle and health checks.

## Strong frontend/type-safety story

> The React app keeps fetch logic in a typed API client instead of scattering it through presentational components. DTOs live in `types.ts`, transport and error mapping live in `reviewApi.ts`, and hooks/components represent async UI state with discriminated unions like `AsyncState<T>`. TypeScript makes impossible UI states harder to represent, while runtime validation remains necessary at the network boundary because JSON is still untrusted.

## What is not production yet?

- no real operational integrations;
- no enterprise auth;
- no production audit store;
- no deployed monitoring stack;
- no cloud orchestration target;
- no real data access;
- no compliance approval;
- small synthetic benchmark.

Use this phrase:

> It is production-shaped, not production-deployed.

## What would you improve next?

Current product milestone:

- GitHub Actions for Python, Spring Boot, React, and repo checks;
- health/readiness smoke tests against containers;
- `.env.example`;
- structured operation logs beyond request correlation;
- keep RUNBOOK current.

Later performance milestone:

- Nano latency/cost optimization;
- cache tuning;
- fallback metrics;
- larger holdout set;
- possible production embedding model only if evidence supports it.

## How does pharmacy background help?

It helps distinguish operationally different concepts that look similar technically: product strength versus administered dose, reported symptom versus controlled escalation trigger, missing record review versus non-applicable review, completed external reference review versus unsupported disclosure, and guidance-only questions versus full quality investigations.
