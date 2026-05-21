# Failure Log

This log captures implementation failures found while building the synthetic Compounding Quality RAG proof of concept. Each entry records what failed, why it mattered, how it was fixed, and what should prevent the same issue from returning.

## Current status

- Test suite is passing.
- The project now has schemas, expected outputs, synthetic SOP corpus, ingestion, retrieval, retrieval evaluation, a stubbed pipeline, structured evaluation, checklist generation, final assessment generation, reporting, and a two-phase CLI workflow.
- The current demo boundary remains synthetic only: no real customer data, patient data, pharmacy records, inventory, customer history, or external drug references.

## Failures

### 1. Stale `test_models.py` import referenced `rag_doc_models`

**Symptom:** Tests failed during import because `test_models.py` still referenced an old module name.

**Root cause:** Model/schema files were renamed or reorganized, but the test import was not updated with the code structure.

**Fix:** Updated the stale test import to reference the current schema/model modules.

**Prevention:** Keep schema import tests focused on the current public model surface. When files are renamed, update imports and run the full test suite immediately.

---

### 2. Pipeline hardcoded `top_k=5`

**Symptom:** Retrieval behavior could not be controlled from tests or higher-level pipeline calls.

**Root cause:** The pipeline used a fixed retrieval count instead of passing a configurable `top_k` argument through to retrieval.

**Fix:** Exposed `top_k` as a parameter and passed it into retrieval.

**Prevention:** Add or preserve tests proving that caller-supplied retrieval settings affect the number of evidence chunks returned.

---

### 3. `FileNotFoundError` message mismatch

**Symptom:** A test failed even though the expected exception type was raised.

**Root cause:** The test expected an exact error-message string, but the implementation returned different wording.

**Fix:** Aligned the message expectation with the implementation, or adjusted the assertion to check the stable, meaningful part of the message instead of the entire sentence.

**Prevention:** For error-message tests, prefer checking useful substrings unless exact wording is part of the user-facing contract.

---

### 4. Retrieval tests expected stale SOP IDs

**Symptom:** Retrieval evaluation failed because expected SOP IDs no longer matched the synthetic corpus.

**Root cause:** SOP fixtures or generated IDs changed, but retrieval test expectations still referenced older IDs.

**Fix:** Updated expected retrieval outputs to match the current synthetic SOP corpus.

**Prevention:** Keep canonical retrieval expectations near the corpus fixtures, and update them whenever source IDs or source titles change.

---

### 5. `no hospitalization` triggered escalation due to naive keyword matching

**Symptom:** A review summary saying the pet had `no hospitalization` still triggered the life-threatening/legal risk lane.

**Root cause:** The risk classifier matched severe keywords like `hospitalization` without understanding negation.

**Fix:** Added/updated logic and tests so routine vomiting cases without actual severe triggers route to follow-up rather than automatic escalation.

**Prevention:** Add explicit negated-trigger test cases for hospitalization, death, legal threat, contamination, veterinarian allegation, wrong medication, and wrong patient language. Longer term, prefer structured reviewer findings over free-text keyword matching for escalation-critical facts.

---

### 6. `TypedDict` fixtures needed explicit `list[RetrievalQuestionResult]`

**Symptom:** Type checks or tests failed because fixture lists of dictionaries were inferred too loosely.

**Root cause:** `TypedDict` list inference did not preserve the expected structured type without an explicit annotation.

**Fix:** Added explicit `list[RetrievalQuestionResult]` annotations to the fixtures.

**Prevention:** Type structured fixtures at declaration time, especially when they contain nested dictionaries or TypedDict values.

### 7. Refusal matching failed because exact-match logic was used instead of substring detection

**Symptom:** External-reference, internal-record, and clinical/legal refusal tests failed because unsupported questions were not refused.

**Root cause:** The matching helper compared each term to the entire input string instead of checking whether the term appeared inside the input.

**Fix:** Changed matching logic to detect terms contained within the normalized concern text and restored correct refusal reasons/messages.

**Prevention:** Keep refusal tests for external references, internal record access, and clinical/legal conclusions. Avoid compact matching helpers unless their behavior is covered by tests.

### 8. Severe escalation routing originally depended on free-text keyword scanning

**Symptom:** Negated reviewer statements like “no hospitalization” or “no wrong medication concern” could be misread as positive severe triggers.

**Root cause:** Final risk-lane logic scanned free-text reviewer summaries for severe terms instead of using structured reviewer findings.

**Fix:** Added `severe_triggers_observed` to `ReviewSummary` and updated final assessment logic to escalate only when a structured severe trigger is supplied.

**Prevention:** Keep tests proving that negated severe-trigger language does not escalate, while explicit structured triggers still do.

## Follow-up lessons

- Tests are most valuable when they protect workflow behavior, not incidental implementation wording.
- Retrieval expectations should be treated as contract fixtures and updated intentionally with corpus changes.
- Safety-critical routing should avoid bare substring matching when negation is likely.
- Demo quality now depends more on the printed report than on additional architecture.
- The project should keep repeating the synthetic-data boundary in CLI output, reports, and demo scripts.
