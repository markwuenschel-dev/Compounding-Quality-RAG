# Failure Log

This log captures implementation failures found while building the synthetic Compounding Quality RAG proof of concept. Each entry records what failed, why it mattered, how it was fixed, and what should prevent the same issue from returning.

## Current status

- Test suite is passing.
- `./gradlew clean test` passes from `services/review-api`.
- The project now has schemas, expected outputs, synthetic SOP corpus, ingestion, retrieval, retrieval evaluation, a stubbed pipeline, structured evaluation, checklist generation, final assessment generation, reporting, a two-phase CLI workflow, and OpenAI-backed review-summary extraction.
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

---

### 9. Coordinated negation scope caused false severe-trigger extraction

**Symptom:** Review-summary extraction could incorrectly preserve or infer `wrong_patient_or_wrong_medication` when a reviewer note used a negated list such as “No hospitalization, death, legal threat, contamination, wrong medication concern, or veterinarian allegation was reported.”

**Root cause:** The severe-trigger grounding logic checked only a short local prefix near the trigger term. In a coordinated list, the negation word appeared earlier in the sentence and fell outside that local window. A wrong-medication special case then made the false positive easier to preserve.

**Fix:** Expanded negation handling to recognize coordinated negation scope across severe-trigger lists, including patterns such as “No A, B, C, or D was reported” and “Reviewer has not confirmed A, B, C, or D.” Added an overcorrection test to confirm that a later affirmative sentence such as “Reviewer confirmed possible wrong medication” still creates the structured severe trigger.

**Prevention:** Keep explicit tests for negated severe-trigger lists and separate tests for confirmed severe triggers after unrelated negated triggers. Escalation-critical extraction should prefer structured, affirmative findings over bare keyword presence.

---

### 10. Retrieval misses for blank review and temperature-excursion boundary

**Symptom:** Retrieval evaluation returned `hit_rate@5 = 0.833` and `MRR = 0.750`, with misses on `RET-007` and `RET-009`.

**RET-007 query:** `two star customer review with no review text should be documented`

**RET-007 expected source:** `SOP-006`

**RET-007 root cause:** `SOP-006` contained the general concept that low-star reviews with no text do not automatically require outreach, but it did not contain enough explicit wording for one-star, two-star, three-star-with-no-text, document-only, or no-Technical-Services-outreach cases. Keyword retrieval therefore lacked direct lexical hooks.

**RET-007 fix:** Added explicit `SOP-006` language for low-star reviews with no review text. The updated SOP states that one-star and two-star reviews, and three-star reviews with no review text, may be documented without Technical Services outreach when no quality concern, safety concern, suspected ADE, product defect, dispensing error, contamination, or escalation trigger is identified.

**RET-009 query:** `temperature excursion outside limited guidance window unsupported product specific stability`

**RET-009 expected source:** `SOP-005` for unsupported product-specific stability. `SOP-006` may also be expected only when the query or test is explicitly checking frontline guidance, document-only handling, or no Technical Services outreach.

**RET-009 root cause:** Temperature-excursion guidance was under-specified in the corpus. The intended rule was that the synthetic corpus supports only a limited 72-hour room-temperature excursion; product-specific stability outside that limited window is unsupported and should not be inferred.

**RET-009 fix:** Added explicit `SOP-005` language for the temperature-excursion boundary. The updated SOP states that the assistant must not infer product-specific stability outside the limited 72-hour room-temperature window or differentiate by dosage form, storage condition, refrigeration requirement, formulation, medication, API, or product-specific stability profile unless supported synthetic source text is present. Added `SOP-006` language for document-only and frontline guidance handling when Technical Services outreach is not supported.

**Prevention:** Retrieval eval questions should only expect sources that actually contain the supporting policy concept. When a query combines unsupported-evidence boundaries with routing behavior, either split the query or include all expected source concepts in the query text. Fix corpus/source-truth gaps before using embeddings to compensate for poor source coverage.


---

### 11. Expected-output tests became brittle around enum casing

**Symptom:** Tests failed after schema values such as QRE/ADE casing were treated as implementation mistakes even though `app/schemas.py` was the intended source of truth.

**Root cause:** Tests validated fixture literals too directly and made the expected-output JSON files act like a competing schema definition.

**Fix:** Added test helper normalization so expected-output fixtures are normalized to current schema enum values at test load time. Evaluation and pipeline tests now test behavior against the schema instead of forcing fixture casing to drive production enums.

**Prevention:** Treat `app/schemas.py` as the controlled source of truth. Fixture normalization is acceptable in tests, but production schema values should not be changed just to satisfy brittle fixture literals.

---

### 12. CLI and reporting tests overfit incidental formatting

**Symptom:** Tests failed when headings, capitalization, or report wording changed even though the workflow behavior still worked.

**Root cause:** Tests asserted presentation copy instead of stable behavior and contract-level structure.

**Fix:** Updated CLI/reporting tests to check stable signals: phase labels, boundary text, evidence visibility, absence of debug scores by default, and generated review checks.

**Prevention:** Exact-match public prose only when that prose is itself the contract. Otherwise prefer structural assertions and key concepts.

---

### 13. API runner needed clear stdout/stderr and exit-code rules

**Symptom:** The bridge needed to be safe for future Java process parsing, but ordinary Python logging or tracebacks on stdout would break JSON parsing.

**Root cause:** A subprocess bridge creates two contracts at once: process-level behavior and application-level JSON behavior. Without explicit rules, those concerns blur.

**Fix:** Added `app/api_runner.py` with a request envelope, success/error response envelopes, stdout-only JSON, stderr diagnostics, handled errors with exit code 0, and unexpected failures with a nonzero exit code plus JSON error output.

**Prevention:** Keep `tests/test_api_runner.py` focused on bridge invariants: stdout is valid JSON, handled errors return `ok:false`, refusal returns structured details, and unexpected exceptions do not leak tracebacks into stdout.

---

### 14. Spring error-handler tests were obscured by test-slice setup and diagnostic code

**Symptom:** `GlobalExceptionHandlerTest` first failed with a `404` for `/test/validate`, then later the generic-error test surfaced a `ServletException`/`AssertionError` instead of the intended centralized JSON response.

**Root cause:** The nested `TestController` was not registered in the `@WebMvcTest` slice until it was explicitly imported. Temporary diagnostic code also remained in the test and generic exception handler, so the diagnostics proved the handler path but deliberately crashed the test instead of returning the API error shape.

**Fix:** Imported `GlobalExceptionHandlerTest.TestController` alongside `GlobalExceptionHandler`, restored real MockMvc assertions for the validation test, and replaced the diagnostic generic handler with a normal `buildResponse(HttpStatus.INTERNAL_SERVER_ERROR, "Unexpected server error", request, List.of())` path. The full `services/review-api` clean test run now passes.

**Prevention:** Keep diagnostic assertions temporary and remove them once the failing path is identified. For `@WebMvcTest`, explicitly import nested test controllers or use a top-level controller fixture when the test depends on custom routes. Keep a targeted `GlobalExceptionHandlerTest` class covering validation, malformed JSON, response-status errors, and generic fallback behavior.
