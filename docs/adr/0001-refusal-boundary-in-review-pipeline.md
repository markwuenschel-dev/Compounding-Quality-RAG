# ADR 0001 — The refusal boundary lives inside the review pipeline seam

- Status: Accepted
- Date: 2026-07-01

## Context

The review stages (validate → refusal boundary → build checklist → final assessment) were
hand-assembled independently in three composition roots: the stdin bridge (`api_runner`), the
FastAPI app (`server`), and the demo `cli`. The sequence drifted: `api_runner` and `cli`
enforced the refusal boundary, but `server`'s `/checklist`, `/retrieve`, and
`/final-assessment` endpoints did not — an unsafe concern (e.g. a request to read a real
compounding record) was answered instead of refused. `ReviewWorkflow` owned the checklist
sequence for one adapter only and exposed its own error-code vocabulary
(`WorkflowRequestError`), which `api_runner` then had to translate back into
`BridgeRequestError` — a seam that existed only to undo the workflow's own error names.

The root cause: no module owned orchestration, so the refusal boundary was a caller's
responsibility, and one caller forgot.

## Decision

Introduce a single **review pipeline** module (`app/review_pipeline.py`) that owns the review
orchestration seam. It validates input, enforces the **refusal boundary**, and sequences the
stages exactly once. Adapters call into it and become thin transport.

The pipeline exposes **semantic outcomes, not transport codes**: it returns the domain
`IntakeChecklist` on success and raises `ReviewRefused` (carrying the full `RefusalResult`) or
`ValueError`. Each adapter maps those to its own protocol (`api_runner` → `REFUSED` /
`INVALID_REQUEST`; `server` → HTTP 403 / 400). The pipeline never invents adapter-facing code
strings, so no translation table is required.

This slice migrates the **checklist** path: `server.py /checklist` and `ReviewWorkflow` now
route through the pipeline. `retrieve` and `final_assessment` are follow-up slices.

## Consequences

- The refusal boundary cannot be skipped by an adapter; `server.py /checklist` now refuses
  unsafe concerns (403). This is a safety fix, covered by the first tests to exercise
  `server.py`.
- Presentation stays with the adapter: the pipeline returns the domain object, and each
  adapter serializes it (raw model vs the camelCase review contract) as its transport needs.
- `ReviewWorkflow` is retained for now as a thin delegator over the pipeline; collapsing it
  entirely, and migrating the `retrieve` / `final_assessment` paths, are deliberate follow-ups.

## Why record this

A future maintainer or architecture review would otherwise wonder why the refusal boundary
lives in the pipeline rather than in each API layer, and might re-scatter it. It lives in the
pipeline precisely so it cannot be forgotten.
