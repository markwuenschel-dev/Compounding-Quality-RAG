# Failure Log

Updated: 2026-06-25

This log captures implementation failures found while building the synthetic Compounding Quality Review Workbench.

Each entry uses:

- **Symptom**
- **Root cause**
- **Fix**
- **Prevention**

## Current status

- Public boundary remains synthetic only.
- React, Spring Boot, and Python now run as separate Docker Compose services.
- Spring calls Python FastAPI over HTTP through `HttpRagEngineClient`.
- Request correlation propagates through `X-Request-Id` across Spring and Python logs.
- Development review-summary extraction passes all 20 adjudicated development cases.
- Retrieval experimentation is closed for the current product milestone: Nano semantic intent is strongest measured frozen-holdout path; rule intent remains fallback.
- Current product focus is operational hardening: CI, container smoke tests, `.env.example`, runbook maintenance, and structured operation logs beyond request correlation.

## Failures

### 1. Stale `test_models.py` import referenced `rag_doc_models`

**Symptom:** Tests failed during import because `test_models.py` still referenced an old module name.

**Root cause:** Model/schema files were renamed or reorganized, but the test import was not updated.

**Fix:** Updated the stale import.

**Prevention:** Run the full test suite immediately after renames.

---

### 2. Pipeline hardcoded `top_k=5`

**Symptom:** Retrieval count could not be controlled from tests or callers.

**Root cause:** Pipeline used a fixed retrieval count.

**Fix:** Exposed `top_k` and passed it into retrieval.

**Prevention:** Keep tests proving caller-supplied retrieval settings affect returned evidence count.

---

### 3. `FileNotFoundError` message mismatch

**Symptom:** Test failed even though the expected exception type was raised.

**Root cause:** Test asserted exact wording instead of stable contract.

**Fix:** Aligned the expectation or asserted a stable substring.

**Prevention:** Do not assert entire error sentences unless wording is part of the user-facing contract.

---

### 4. Retrieval tests expected stale SOP IDs

**Symptom:** Retrieval evaluation failed because expected source IDs no longer matched the corpus.

**Root cause:** SOP fixtures changed but expectations were stale.

**Fix:** Updated expected outputs to match current synthetic corpus.

**Prevention:** Treat retrieval expectations as contract fixtures and update intentionally with corpus changes.

---

### 5. `no hospitalization` triggered escalation

**Symptom:** A note saying `no hospitalization` triggered severe escalation.

**Root cause:** Risk classifier matched severe keywords without negation.

**Fix:** Added logic/tests so negated severe terms do not escalate.

**Prevention:** Keep explicit negated-trigger tests for hospitalization, death, legal threat, contamination, veterinarian allegation, wrong medication, and wrong patient.

---

### 6. `TypedDict` fixtures needed explicit list annotations

**Symptom:** Type checks failed because fixture lists were inferred too loosely.

**Root cause:** `TypedDict` inference did not preserve nested structure.

**Fix:** Added explicit `list[RetrievalQuestionResult]` annotations.

**Prevention:** Type structured fixtures at declaration time.

---

### 7. Refusal matching used exact-match logic

**Symptom:** Unsupported real-record/external-reference/clinical-legal questions were not refused.

**Root cause:** Helper compared each term to the entire input string instead of checking containment.

**Fix:** Changed matching to detect terms inside normalized concern text.

**Prevention:** Keep refusal tests for external references, internal record access, and clinical/legal conclusions.

---

### 8. Severe routing depended on free-text scanning

**Symptom:** Negated severe phrases could be treated as positive severe triggers.

**Root cause:** Final risk-lane logic scanned free text instead of structured findings.

**Fix:** Added `severe_triggers_observed` and routed severe escalation from that structured field.

**Prevention:** Keep tests for negated severe language and explicit structured triggers.

---

### 9. Coordinated negation scope caused false severe extraction

**Symptom:** A negated list like `No hospitalization, death, legal threat, contamination, wrong medication concern, or veterinarian allegation was reported` could still create a severe trigger.

**Root cause:** Negation handling checked only a short local prefix near the term.

**Fix:** Expanded coordinated-list negation handling and added overcorrection tests.

**Prevention:** Test negated lists and later affirmative triggers separately.

---

### 10. Retrieval misses exposed source-truth gaps

**Symptom:** Keyword retrieval missed blank low-star review guidance and unsupported temperature-excursion stability boundaries.

**Root cause:** SOP text lacked explicit lexical support for intended policies.

**Fix:** Added narrow SOP language for those policies.

**Prevention:** Fix missing source-truth before using embeddings or semantic interpretation to compensate.

---

### 11. Completed external-reference review had no controlled value

**Symptom:** Completed outside reference reviews were inconsistently labeled.

**Root cause:** Enum represented synthetic consulted and external needed, but not external already consulted.

**Fix:** Added `external_reference_consulted` and precedence rules.

**Prevention:** Keep tests for all reference states and non-disclosure override.

---

### 12. Explicit unresolved commands were not extracted

**Symptom:** Notes containing `Confirm`, `Clarify`, or `Determine whether` missed `missing_information`.

**Root cause:** Detector did not recognize canonical command wording.

**Fix:** Expanded explicit-missing detection and normalized labels.

**Prevention:** Maintain table-driven tests for canonical unresolved-question phrases.

---

### 13. Device and dose matching used overly broad lexical signals

**Symptom:** `suspension`/`clicks`/strength/package values produced wrong device or dose fields.

**Root cause:** Device and dose rules used broad lexical cues without context.

**Fix:** Added word boundaries, device-failure context, and administration-context requirements.

**Prevention:** Keep negative tests for suspension, click dosing, product strength, package quantity, and non-device transdermal concerns.

---

### 14. Review-summary silence was inconsistent

**Symptom:** Guidance-only cases were marked incomplete while ADE/product-quality cases were marked `not_applicable`.

**Root cause:** No deterministic policy decided whether silence meant irrelevant or undocumented.

**Fix:** Added review-scope inference and defaults.

**Prevention:** Test guidance-only and full-investigation cases in parallel.

---

### 15. Worksheet review was overwritten as incomplete

**Symptom:** `Worksheet review found no discrepancy` became `documentation_incomplete`.

**Root cause:** Matcher did not recognize worksheet review as record review.

**Fix:** Added worksheet-review alias and regression test.

**Prevention:** Add domain aliases only from observed cases and protect each with tests.

---

### 16. Explicit same-lot pattern remained unavailable

**Symptom:** `One additional quality complaint was identified for the lot` remained `unavailable`.

**Root cause:** Policy detected lot info but did not normalize value.

**Fix:** Added deterministic lot-pattern grounding.

**Prevention:** Separate tests for field presence and value normalization.

---

### 17. Patch packages installed tests before runtime changes

**Symptom:** New tests failed because implementation files still had old code.

**Root cause:** Patch required a second application step, leaving repo partially migrated.

**Fix:** Added fail-closed repair scripts and later used complete replacement files for isolated changes.

**Prevention:** Prefer atomic verified migrations. Do not declare success until implementation and tests are present.

---

### 18. UI container copied host `node_modules`

**Symptom:** React/Vite container could fail with platform-specific host dependencies.

**Root cause:** Docker used repo-root context, but only service-local `.dockerignore` files existed.

**Fix:** Added repo-root `.dockerignore`.

**Prevention:** Root `.dockerignore` is authoritative when Compose services build with `context: ..`.

---

### 19. Extraction returned 502 in container due missing model config

**Symptom:** Review-summary extraction failed through Spring with downstream engine error.

**Root cause:** Python container did not receive `OPENAI_API_KEY`.

**Fix:** Wired `rag-engine-python/secrets.env` through Compose `env_file`.

**Prevention:** Keep `.env.example` synchronized with required variables and add endpoint smoke tests.

---

### 20. Logs lacked end-to-end request correlation proof

**Symptom:** Same failing request could not be reliably connected across Spring/Python logs.

**Root cause:** Request ID lifecycle, MDC, downstream propagation, and Python log echoing were not all proven.

**Fix:** Added Spring request filter, MDC, response/header echo, HTTP client propagation, Python middleware logging, and smoke test.

**Prevention:** Keep boundary tests and smoke test. Treat this as correlation, not full tracing.

---

### 21. Documentation became stale after HTTP migration

**Symptom:** Docs still described manual startup, CLI runner, stale retrieval bottlenecks, or subprocess bridge details.

**Root cause:** Implementation moved faster than docs.

**Fix:** Updated active docs for HTTP boundary, Docker Compose, request correlation, retrieval-intent decision, and operational-hardening milestone.

**Prevention:** After architecture-changing PRs, update README, RUNBOOK, DECISIONS, data dictionary, demo script, and interview framing before closing milestone.

## Lessons

- Tests should protect workflow behavior, not incidental wording.
- Retrieval expectations are contract fixtures.
- Safety-critical routing should avoid bare substring matching.
- HTTP service boundaries require readiness, timeouts, error translation, and request correlation.
- Docker Compose proves local orchestration, not production deployment.
- Documentation staleness is a defect when it misrepresents architecture or limitations.
