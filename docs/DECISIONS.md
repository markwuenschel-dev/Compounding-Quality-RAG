# Decisions

## 2026-05-04 — Project boundary

### Decision
This project will be a source-grounded RAG workbench for synthetic pharmacy/compounding SOP-style documents and synthetic inquiry records.

### Reason
Synthetic documents are safe to publish and let me control the document structure, expected answers, review states, and evaluation cases. The public project can model the workflow shape without exposing proprietary records, internal SOP text, customer information, PHI, PII, or licensed drug-information content.

### Alternatives considered
- Public pharmacy/regulatory documents
- Internal documents
- Generic legal/compliance documents

### Tradeoff
Synthetic documents are safer but less realistic than real regulatory, operational, or customer-review material.

### Revisit when
The ingestion, chunking, retrieval, and evaluation loop works on the synthetic corpus.

---

## 2026-05-04 — Initial document schema

### Decision
The first core objects are `SourceDocument` and `DocumentChunk`, followed by more specific objects for SOP documents and synthetic inquiry records.

### Reason
The RAG system needs a clear boundary between a full source document, a synthetic inquiry record, and the smaller chunks used for retrieval.

### Alternatives considered
- Use raw dictionaries: simplest method, but there is no validation or enforced structure. Misspellings in keys or missing fields will not fail early and can cause runtime errors later.
- Use dataclasses: dataclasses provide structured objects and type hints, but they do not enforce validation by default. Additional validation would need to be implemented manually, which recreates functionality already provided by Pydantic.
- Delay schema design until ingestion is built.

### Tradeoff
Pydantic introduces runtime validation overhead when creating objects, but early validation is worth it for an accuracy-sensitive RAG system because malformed SOPs or inquiry records should fail before they can enter retrieval.

### Revisit when
The first loader and chunker are working.

---

## 2026-05-04 — Testing approach

### Decision
Start with small pytest tests for model validation.

### Reason
The immediate goal is to learn the pytest pattern and prove that invalid chunks, SOPs, and inquiry records fail early.

### Alternatives considered
- No tests until retrieval works
- Only manual testing
- Larger integration tests immediately

### Tradeoff
These tests are simple and do not prove the RAG system works yet.

### Revisit when
The loader and chunker exist.

---

## 2026-05-09 — Formal classification versus handling path

### Decision
Separate formal QRE classification from operational handling path.

### Reason
The formal QRE/general-question label and QRE category/subcategory are documentation concepts. They do not always determine the Technical Services workflow. A submission can arrive through the same form but require different review depth depending on concern type, risk lane, missing information, and escalation triggers.

### Consequence
Synthetic inquiry records will store formal classification separately from concern type, risk lane, review scope, investigation requirements, handling path, and resolution options.

### Tradeoff
This makes the schema more verbose, but prevents a single overloaded `disposition` field from mixing documentation category, workflow action, escalation state, and customer-facing resolution.

### Revisit when
Evaluation questions show the model is confusing classification, handling path, and resolution.

---

## 2026-05-09 — Risk lane model

### Decision
Use `risk_lane` as a severity and escalation guide separate from formal category and handling path.

### Reason
The real workflow behaves like a risk-tiered investigation. Expected/self-limiting concerns require less aggressive review than unexpected or life-threatening/legal concerns, even when they arrive through the same intake channel.

### Allowed values
- `expected_self_limiting`
- `unexpected_non_life_threatening`
- `life_threatening_or_legal`

### Consequence
Synthetic inquiries can model different investigation paths without pretending every concern has a clean final disposition at intake.

### Tradeoff
Risk lane is a derived assessment, not a raw intake field. In intake-only records it should usually be null until enough information exists to support it.

### Revisit when
The first intake/checklist mode produces useful missing-information outputs.

---

## 2026-05-09 — Carry-forward inquiry schema

### Decision
Use one carry-forward schema for synthetic inquiries rather than two unrelated sets of records.

### Reason
A real inquiry changes state over time. At intake, only raw form or review information may be available. After Technical Services review, the record can carry review-summary findings. After assessment, it can carry derived classification, risk lane, handling path, and rationale.

### Consequence
Synthetic inquiry records include `workflow_stage`:
- `intake_only`
- `review_summary_complete`
- `finalized`

For `intake_only` records, `review_summary` and `derived_assessment` may be null. Later versions of the same record can fill those sections in.

### Tradeoff
The YAML files are not meant to be the real user interface. They are a portfolio-friendly stand-in for a database record, form, or review note interface.

### Revisit when
Loaders and validation make the carry-forward shape feel too complex or too permissive.

---

## 2026-05-09 — Frontline pharmacist questions

### Decision
Do not model frontline pharmacist questions as a separate intake source.

### Reason
Frontline pharmacist questions arrive through the QRE/general-question submission form. They differ by submitter role, submission purpose, and review scope, not by ingestion channel.

### Consequence
Synthetic inquiry records use:

```yaml
intake_source: qre_general_question_form
submitter_role: frontline_pharmacist
submission_purpose: frontline_pharmacist_question
review_scope: guidance_only
```

These records usually do not require compounding-record review, lot/batch review, inventory inspection, trend scan, or customer outreach unless the narrative alleges a product quality issue, ADE, dispensing error, or escalation trigger.

### Tradeoff
This adds fields, but preserves the real workflow and still allows tracking the volume of frontline pharmacist questions.

### Revisit when
Analytics or validation shows `submission_purpose` and `review_scope` are redundant.

---

## 2026-05-09 — Synthetic review summaries instead of fake system access

### Decision
The public project will not pretend the RAG system has access to compounding records, lot-tracing systems, customer histories, inventory, Snowflake, or external drug-information resources.

### Reason
The public portfolio project must be synthetic and safe. Real-world integrations would require approved data access, governance, security review, and system-specific API design.

### Consequence
Synthetic inquiry records may include a `review_summary` object that represents human-entered or synthetic findings after review. The RAG system can use those summaries, but it should not claim it directly inspected real operational systems.

### Tradeoff
This is less impressive than direct integration, but more accurate and safer. It also keeps the first portfolio version focused on retrieval, validation, citation, and workflow reasoning.

### Revisit when
A private/internal prototype is approved and read-only integration requirements are known.

---

## 2026-05-09 — Resolution options separate from handling path

### Decision
Keep customer-facing resolution options separate from operational handling path.

### Reason
Handling path describes what Technical Services does next. Resolution options describe possible case-closure or customer-facing actions such as counseling, replacement/reship review, refund/concession review, or alternate dosage form discussion.

### Consequence
Synthetic inquiry records may include:

```yaml
handling_path: technical_services_customer_outreach
resolution_review_required: true
resolution_options:
  - alternate_dosage_form_discussion
  - refund_or_concession_review
```

### Tradeoff
This avoids overloading `handling_path`, but it requires answer rules to clearly distinguish workflow action from customer resolution.

### Revisit when
Synthetic inquiries and evaluation questions reveal duplicate or confusing resolution values.

## 2026-05-18 — Structured severe escalation triggers

### Decision
Use `review_summary.severe_triggers_observed` as the structured source of truth for severe escalation routing.

### Reason
Free-text reviewer summaries can contain negated severe terms such as “no hospitalization,” “no death,” “no legal threat,” or “no wrong medication concern.” Keyword scanning can misread those phrases as positive escalation evidence.

### Consequence
Final risk-lane logic escalates to `life_threatening_or_legal` when `severe_triggers_observed` is non-empty. Negated free-text statements do not independently trigger escalation. The reviewer or future extraction layer must explicitly populate the structured trigger list.

### Tradeoff
This requires one additional structured reviewer field, but it is safer and easier to validate than brittle free-text parsing.

### Revisit when
The LLM review-summary extraction layer is added and must map normal English reviewer notes into `ReviewSummary`.

---

## 2026-05-26 — Intake understanding as schema-validated LLM extraction

### Decision
Add `IntakeUnderstanding` as a schema-level contract and route Phase 1 intake text through an optional OpenAI-backed structured extraction layer before checklist generation.

### Reason
The initial checklist should not ask for facts already supplied in the concern text, such as species, dosage form, flavor, timing, or symptom course. A typed extraction layer lets the project capture those facts once, validate them with Pydantic, and pass them into deterministic checklist logic without making the LLM the decision engine.

### Consequence
`app/extract_intake_understanding.py` owns prompt construction, JSON parsing, and `IntakeUnderstanding` validation. The module may identify a possible semantic boundary issue, but downstream application logic still owns refusal handling, checklist generation, final assessment routing, and safety-critical decisions.

### Alternatives considered
- Hard-code a deterministic keyword-based intake fact extractor.
- Expand checklist heuristics directly.
- Let the LLM generate the checklist.

### Tradeoff
The OpenAI extraction layer improves semantic understanding but adds dependency, latency, and failure modes. The CLI therefore keeps deterministic refusal first and can continue checklist generation if optional intake understanding is unavailable.

### Revisit when
The Spring Boot API exposes checklist generation and the request/response DTOs need to represent intake understanding explicitly.
