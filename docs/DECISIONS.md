# Decisions

Updated: 2026-06-25

This file records stable technical decisions. Use the failure log for defects and repairs.

## 2026-05-04 — Project boundary

### Decision

This project is a source-grounded AI review workbench for synthetic pharmacy/compounding SOP-style documents and synthetic inquiry records.

### Reason

Synthetic documents are safe to publish and let the project control document structure, expected answers, review states, and evaluation cases without exposing proprietary records, internal SOP text, customer information, PHI, PII, or licensed drug-information content.

### Tradeoff

Synthetic data is safer but less realistic than real operational material.

### Revisit when

A private/internal prototype is approved with governed read-only data access.

---

## 2026-05-04 — Schema-first model

### Decision

Use validated schema objects for documents, chunks, inquiries, review summaries, derived assessments, and expected outputs.

### Reason

Malformed records should fail before entering retrieval, extraction, or evaluation.

### Tradeoff

Pydantic adds runtime validation overhead, but the safety and debugging benefits are worth it.

---

## 2026-05-09 — Separate classification from handling path

### Decision

Separate formal QRE/general-question classification from operational handling path.

### Reason

Formal classification is documentation. Handling path is workflow. One overloaded field would mix category, risk, escalation, and customer-resolution concepts.

---

## 2026-05-09 — Risk lane model

### Decision

Use `risk_lane` as a severity/escalation guide separate from formal category and handling path.

### Values

- `expected_self_limiting`
- `unexpected_non_life_threatening`
- `life_threatening_or_legal`

### Reason

Review depth is risk-tiered and cannot be inferred from intake channel alone.

---

## 2026-05-09 — Frontline pharmacist questions use shared intake source

### Decision

Do not model frontline pharmacist questions as a separate intake source.

### Reason

They arrive through the QRE/general-question form and are distinguished by submitter role, submission purpose, and review scope.

### Canonical shape

```yaml
intake_source: qre_general_question_form
submitter_role: frontline_pharmacist
submission_purpose: frontline_pharmacist_question
review_scope: guidance_only
```

---

## 2026-05-09 — Synthetic review summaries instead of fake system access

### Decision

The public project does not pretend to access compounding records, lot-tracing systems, customer histories, inventory, Snowflake, external drug-information resources, or licensed references.

### Consequence

The tool can use human-entered or synthetic `review_summary` findings, but it must not claim direct access to real operational systems.

---

## 2026-05-18 — Structured severe escalation triggers

### Decision

Use `review_summary.severe_triggers_observed` as the structured source of truth for severe escalation routing.

### Reason

Free text can contain negated severe terms such as “no hospitalization.” Keyword scanning is unsafe for escalation-critical facts.

---

## 2026-06-09 — Preserve keyword retrieval as baseline

### Decision

Keep keyword retrieval as the transparent baseline behind `KeywordRetriever`.

### Reason

Keyword retrieval is interpretable, auditable, and useful for exact SOP/process terms.

---

## 2026-06-09 — Add local deterministic vector and hybrid baselines

### Decision

Add local hashing-vector `EmbeddingRetriever` and normalized-score `HybridRetriever` as evaluation baselines before adding external embedding models or vector databases.

### Reason

The project needs retrieval plumbing and comparison infrastructure before infrastructure complexity.

### Tradeoff

The hashing-vector model is not production semantic search and must not be described as such.

---

## 2026-06-15 — Hybrid review-summary extraction

### Decision

Use the LLM to propose a structured `ReviewSummary`, then apply Pydantic validation and deterministic grounding.

### Reason

Flexible language belongs to the LLM; high-impact workflow semantics such as negation, same-lot patterns, reference states, missing checks, and severe triggers need repeatable policy.

### Architecture

```text
LLM candidate -> schema validation -> deterministic grounding -> review-scope defaults
```

---

## 2026-06-15 — Reference-review states and precedence

### Decision

Add `external_reference_consulted` and use this precedence:

1. unsupported or non-disclosure boundary;
2. completed external review;
3. completed synthetic-corpus review;
4. external review still needed;
5. no reference review needed.

### Reason

Completed external review is different from external review still needed.

---

## 2026-06-15 — Scope-first defaults

### Decision

Infer guidance-only versus full investigation before defaulting undocumented review-summary fields.

### Full investigation defaults

- absent record result -> `documentation_incomplete`
- absent lot result -> `unavailable`
- absent inventory result -> `not_checked`
- absent reference result -> `not_needed`

### Guidance-only defaults

- absent record/lot/inventory -> `not_applicable`
- absent reference -> `not_needed`

---

## 2026-06-15 — Complaint-reported severe triggers

### Decision

A listed severe trigger reported in the complaint, such as hospitalization, may be proposed immediately for reviewer confirmation.

### Boundary

Shortness of breath, collapse, falling over, and similar symptoms remain context unless tied to an existing structured trigger.

---

## 2026-06-15 — Development and holdout separation

### Decision

Use development fixtures for tuning and holdout fixtures for generalization estimates.

### Consequence

After a holdout result is used to design a fix, that dataset becomes a regression benchmark. New generalization claims require a new untouched holdout.

---

## 2026-06-23 — HTTP service boundary and Docker Compose stack

### Decision

Replace the in-process Python subprocess bridge with an HTTP FastAPI service called by Spring Boot, and run React, Spring, and Python under Docker Compose.

### Reason

The subprocess bridge coupled Spring to Python interpreter discovery, working directory, and stdout/stderr parsing. HTTP gives each service an independent lifecycle and health surface.

### Consequence

- Python engine runs as FastAPI `app/server.py`.
- `api_runner.py` remains legacy/local CLI only.
- Spring calls Python through `HttpRagEngineClient`.
- `PYTHON_ENGINE_BASE_URL` controls the boundary.
- Docker Compose provides health-gated local startup.

---

## 2026-06-23 — Retrieval intent ablation decision

### Decision

Use Nano semantic intent as the current accuracy-oriented retrieval interpretation path, rule intent as deterministic fallback, and keyword retrieval as the unchanged retriever after vocabulary mapping.

### Frozen holdout result

| Strategy | Hit rate@5 | MRR | Negative pass |
|---|---:|---:|---:|
| Raw | 0.700 | 0.567 | 0.850 |
| Deterministic expansion | 0.850 | 0.733 | 0.850 |
| Rule intent | 0.750 | 0.725 | 0.900 |
| Nano intent | 0.950 | 0.950 | 1.000 |

### Runtime path

```text
Nano semantic intent -> deterministic workflow derivation -> vocabulary mapper -> keyword retrieval
```

Fallback path:

```text
Rule semantic intent -> deterministic workflow derivation -> vocabulary mapper -> keyword retrieval
```

### Tradeoff

Nano improves measured generalization but adds latency, cost, external dependency, and cache/fallback complexity. Further Nano optimization belongs in a later performance milestone.

---

## 2026-06-24 — Request correlation across Spring and Python

### Decision

Propagate `X-Request-Id` across Spring and Python and include it in logs and response headers.

### Reason

A multi-service local stack needs a way to connect UI/API requests, Spring logs, downstream Python calls, and error responses.

### Boundary

This is request correlation, not full distributed tracing.

---

## 2026-06-25 — Documentation consolidation

### Decision

Keep a small active documentation set and archive stale repair/proposal/history docs.

### Reason

The risk has shifted from missing documentation to stale documentation. Docs that still describe the subprocess bridge, old retrieval bottlenecks, or proposed policies can mislead reviewers.

### Active docs

- `README.md`
- `RUNBOOK.md`
- `docs/data_dictionary.md`
- `docs/Workflow_Taxonomy_Reference.md`
- `docs/DECISIONS.md`
- `docs/failure_log.md`
- `docs/interview_framing.md`
- `docs/retrieval_query_ablation_design.md`
- `docs/evaluation_case_authoring.md`
- `docs/holdout_case_capture_worksheet.md`
- focused policy docs only while synchronized with the data dictionary
