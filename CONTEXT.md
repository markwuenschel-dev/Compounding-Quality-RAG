# Domain Context

Ubiquitous language for the Compounding Quality RAG engine. Use these terms in code,
tests, and review. This file is consulted by architecture reviews to name good seams.

## Terms

**Review pipeline** — the single module (`rag-engine-python/app/review_pipeline.py`) that
owns review orchestration: it sequences input validation, the refusal boundary, and the
deterministic stages (checklist today; final assessment and retrieval to follow) in one
place. Adapters — the stdin bridge (`api_runner`), the FastAPI app (`server`), and the demo
`cli` — call into the pipeline rather than assembling the stages themselves, so the sequence
cannot drift apart between them.

**Refusal boundary** — the policy seam that blocks a concern the system must not answer
(external drug-reference lookups, internal-record access, clinical/legal conclusions). It is
enforced *inside the review pipeline*, not in the adapters, so no transport can forget it.
Crossing the boundary surfaces as the `ReviewRefused` domain outcome, which each adapter maps
to its own transport (bridge `REFUSED`, HTTP 403).

**Intake checklist** — the deterministic, evidence-cited review checklist built from a
concern (`build_intake_checklist` → `IntakeChecklist`). It is the domain result of the
checklist stage; how it is serialized (raw model vs the camelCase review contract) is a
presentation concern owned by the adapter, not the pipeline.
