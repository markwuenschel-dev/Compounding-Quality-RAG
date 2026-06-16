# Failure Log

This log captures implementation failures found while building the synthetic Compounding Quality RAG proof of concept. Each entry records what failed, why it mattered, how it was fixed, and what should prevent the same issue from returning.

## Current status

- The development review-summary extraction benchmark passes all 20 adjudicated cases.
- Retrieval development performance remains the current quality bottleneck.
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

### 11. Completed external-reference review had no controlled value

**Symptom:** Completed USP, manufacturer, veterinary-reference, internal-clinical-guidance, and package-insert reviews were inconsistently labeled as `synthetic_reference_consulted`, `external_reference_needed`, or `not_supported_by_public_corpus`.

**Root cause:** The enum represented a synthetic reference and a still-needed external review, but not an outside reference that had already been consulted.

**Fix:** Added `external_reference_consulted`, defined explicit precedence, and made non-disclosure override completed-review status.

**Prevention:** Keep reference-state tests for not needed, synthetic consulted, external consulted, external still needed, and unsupported/non-disclosable.

---

### 12. Explicit unresolved commands were not extracted

**Symptom:** Investigation notes containing `Confirm`, `Clarify`, or `Determine whether` produced empty or incomplete `missing_information`.

**Root cause:** The explicit-missing detector recognized phrases such as `unknown` and `need to confirm`, but not the canonical command wording used by the generated investigation summaries.

**Fix:** Expanded explicit-missing detection and normalized common investigation questions into stable labels.

**Prevention:** Maintain table-driven tests for every canonical unresolved-question phrase.

---

### 13. Device and dose matching used overly broad lexical signals

**Symptom:** Unrelated oral suspensions and transdermal skin reactions produced `device_dispense_status`, while product strength or package quantity could be mistaken for the administered dose.

**Root cause:** Device logic relied on broad substrings such as `pen` and `clicks`, and dose logic treated any numeric medication unit as an administered dose.

**Fix:** Added word boundaries, required device-failure context, and required administration context for dose detection.

**Prevention:** Keep negative tests for `suspension`, dose instructions using clicks, product strength, package quantity, and non-device transdermal concerns.

---

### 14. Review-summary silence was interpreted inconsistently

**Symptom:** Guidance-only cases were labeled as incomplete investigations, while ADE and product-quality cases with undocumented checks were labeled `not_applicable`.

**Root cause:** The extractor had no deterministic policy for deciding whether an absent result was irrelevant or required-but-undocumented.

**Fix:** Added review-scope inference and conservative defaults for record, lot, inventory, and reference fields.

**Prevention:** Test guidance-only and full-investigation cases in parallel whenever scope rules change.

---

### 15. Explicit worksheet review was overwritten as incomplete

**Symptom:** `Worksheet review found no discrepancy` became `documentation_incomplete`.

**Root cause:** The record-result matcher recognized `record review` and `compounding-record review`, but not the domain synonym `worksheet review`.

**Fix:** Added `worksheet review` as an explicit record-review phrase and added a bridge-level regression test.

**Prevention:** Add domain-language aliases only from observed cases and protect each with a regression test.

---

### 16. Explicit same-lot pattern remained unavailable

**Symptom:** `One additional quality complaint was identified for the lot` remained `unavailable`.

**Root cause:** The policy detected that lot information existed but did not normalize the statement into a controlled lot-pattern value.

**Fix:** Added deterministic positive and negative lot-pattern grounding.

**Prevention:** Separate tests for field presence and value normalization.

---

### 17. Patch packages installed tests before runtime changes

**Symptom:** New fixtures and tests failed because the implementation files still had the old enum, helper signature, and matching behavior.

**Root cause:** The package required an additional application script, and the repository entered a partially migrated state.

**Fix:** Added fail-closed repair scripts, structural verification, Python compilation, and later switched isolated changes to complete replacement files.

**Prevention:** Prefer one atomic verified migration for broad edits and complete replacement files for small edits. Do not declare success until implementation and tests are both present.
