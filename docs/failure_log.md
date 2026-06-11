# Failure Log

This log captures implementation failures found while building the synthetic Compounding Quality RAG proof of concept. Each entry records what failed, why it mattered, how it was fixed, and what should prevent recurrence.

## Current Status

- Python deterministic workflow is implemented for ingestion, retrieval, evaluation, checklist generation, refusal behavior, final assessment, reporting, CLI workflow, optional review-summary extraction, and JSON bridge execution.
- Spring Boot `review-api` loads successfully with the local Python engine configuration and exposes checklist, retrieve, and final-assessment endpoints.
- Retrieval evaluation now includes retriever abstraction, keyword baseline wrapper, local deterministic vector retrieval, hybrid retrieval, comparison scaffold, and generated report output.
- Public demo boundary remains synthetic only.

## 1. Stale import referenced old module

**Symptom:** Tests failed during import.

**Root cause:** Tests referenced a renamed module.

**Fix:** Updated imports to current schema/model modules.

**Prevention:** Run full tests immediately after file/module renames.

## 2. Pipeline hardcoded `top_k=5`

**Symptom:** Retrieval count could not be controlled.

**Root cause:** Fixed value instead of caller-provided parameter.

**Fix:** Exposed `top_k` and passed it through.

**Prevention:** Keep tests proving caller-supplied `top_k` is honored.

## 3. Brittle exact error-message assertion

**Symptom:** Correct exception failed test due to wording mismatch.

**Root cause:** Test asserted exact incidental prose.

**Fix:** Assert stable substrings or contract fields.

**Prevention:** Exact message assertions only when wording is public contract.

## 4. Retrieval tests expected stale SOP IDs

**Symptom:** Retrieval eval failed after corpus/ID changes.

**Root cause:** Expected IDs were not updated with source changes.

**Fix:** Synced expectations with corpus.

**Prevention:** Treat retrieval expectations as source-aligned contract fixtures.

## 5. Negated severe term triggered escalation

**Symptom:** “No hospitalization” still escalated.

**Root cause:** Keyword matching without negation handling.

**Fix:** Severe routing moved toward structured review-summary triggers.

**Prevention:** Keep tests for negated hospitalization, death, legal threat, contamination, wrong-medication, and wrong-patient language.

## 6. Refusal matching used exact match instead of substring detection

**Symptom:** Unsupported record/reference/clinical requests were not refused.

**Root cause:** Matching helper compared term to whole input.

**Fix:** Detect contained normalized terms.

**Prevention:** Keep explicit refusal tests.

## 7. Severe escalation originally depended on free-text scanning

**Symptom:** Free-text negations could be misread.

**Root cause:** Final risk-lane logic scanned prose instead of structured reviewer findings.

**Fix:** Added `severe_triggers_observed` and made it authoritative.

**Prevention:** Escalation-critical facts should be structured.

## 8. Coordinated negation scope failed

**Symptom:** Lists like “No hospitalization, death, legal threat, contamination, or wrong medication” could preserve false triggers.

**Root cause:** Negation detection window was too short.

**Fix:** Expanded coordinated-negation handling and added overcorrection tests.

**Prevention:** Keep separate tests for negated lists and later affirmative trigger statements.

## 9. Retrieval misses exposed corpus wording gaps

**Symptom:** Retrieval missed blank-review and temperature-excursion boundary cases.

**Root cause:** Source corpus did not contain enough explicit lexical support.

**Fix:** Added explicit SOP language.

**Prevention:** Fix source-truth gaps before expecting vector retrieval to compensate.

## 10. Spring MVC validation test returned 404

**Symptom:** Expected validation error, got route not found.

**Root cause:** Test controller was not registered in the WebMvc slice.

**Fix:** Imported/registered the test controller.

**Prevention:** Confirm test route registration before diagnosing validation behavior.

## 11. Bridge stdout pollution caused invalid stdout

**Symptom:** Java client classified bridge output as `ENGINE_INVALID_STDOUT`.

**Root cause:** Stub printed debug text to stdout before JSON.

**Fix:** Keep stdout JSON-only; diagnostics to stderr.

**Prevention:** Preserve stdout-pollution tests.

## 12. Jackson mapping wrapped domain constructor failure

**Symptom:** Test expected direct `IllegalArgumentException`; actual direct cause was Jackson wrapper.

**Root cause:** Generic `treeToValue(...)` mapping wraps record-constructor failures.

**Fix:** Assert public `ENGINE_RESPONSE_MAPPING` and root cause.

**Prevention:** Test public contract, not incidental exception wrapping.

## 13. Mixed Jackson 2 / Jackson 3 broke Spring Boot 4 runtime

**Symptom:** App failed to start because no Jackson 2 `ObjectMapper` bean existed.

**Root cause:** Production requested Jackson 2 while tests/config used Jackson 3.

**Fix:** Migrated bridge/config boundary to Jackson 3 `JsonMapper`.

**Prevention:** Keep one JSON generation at a boundary.

## 14. Missing `@Bean` for `RagEngineClient`

**Symptom:** No `RagEngineClient` bean in Spring context.

**Root cause:** Configuration method lacked `@Bean` after refactor.

**Fix:** Restored `@Bean`.

**Prevention:** Config tests should assert `hasNotFailed()` and `hasSingleBean(RagEngineClient.class)`.

## 15. Interface/implementation drift

**Symptom:** Compile failed because `PythonProcessRagEngineClient` did not implement `retrieve(...)` or `createFinalAssessment(...)`.

**Root cause:** Interface expansion and implementation update drifted.

**Fix:** Replaced both files with matching signatures and implementations.

**Prevention:** Expand interface and implementation in one commit; run `compileJava` before moving on.

## 16. Jackson 3 `JsonNode` compared directly to string

**Symptom:** Test failed comparing string to `JsonNode` object.

**Root cause:** Assertion missed `.asString()`.

**Fix:** Extract scalar string value before comparison.

**Prevention:** Compare JSON scalar values, not node objects.

## 17. `HttpStatus.UNPROCESSABLE_ENTITY` deprecation

**Symptom:** Compile warning.

**Root cause:** Spring Framework 7 deprecated the enum constant.

**Fix:** Use `UNPROCESSABLE_CONTENT` while preserving HTTP 422.

**Prevention:** Fix mechanical deprecations during framework upgrades.

## 18. Spring failed to bind working directory directly to `Path`

**Symptom:** App failed to bind `../../rag-engine-python` to `Path`.

**Root cause:** Spring treated the relative path as resource-style path and rejected normalization.

**Fix:** Bind as `String`; convert with `Path.of(...)` at client properties boundary.

**Prevention:** For relative filesystem paths in Spring config, prefer explicit conversion.

## 19. `checkAll` did not exist from `services/review-api`

**Symptom:** Gradle task not found.

**Root cause:** Command was run in module root where lifecycle task is `check`, not repo-level `checkAll`.

**Fix:** Use `./gradlew check` from `services/review-api`.

**Prevention:** Document commands relative to working directory.

## 20. Retriever abstraction tests imported names before production file was updated

**Symptom:** Tests or type checker reported that `app.retrieval` had no `KeywordRetriever` or `Retriever` attribute.

**Root cause:** Test files referenced the new abstraction while the active imported `app/retrieval.py` was still the old implementation or the environment was importing a different copy.

**Fix:** Confirmed `app.retrieval.__file__`, replaced the active production file, and verified `KeywordRetriever`, `Retriever`, and `retrieve` existed in the same imported module.

**Prevention:** When adding public symbols, verify the active import path and production file before debugging test logic.

## 21. Hit-rate was confused with recall

**Symptom:** A comparison test expected `hit_rate_at_k = 0.5` when one of two expected sources was found.

**Root cause:** The test interpreted hit-rate as “fraction of expected sources found.” The evaluator defines hit-rate as a per-question binary value: at least one expected source in top-k.

**Fix:** Corrected the expected hit-rate to `1.0` when any expected source appears in top-k.

**Prevention:** Keep metric definitions in the taxonomy and data dictionary. Use separate recall@k only if that metric is intentionally added.

## 22. MRR was confused with additive source credit

**Symptom:** A test expected reciprocal-rank credit to combine across multiple expected sources.

**Root cause:** MRR measures the first relevant retrieved result only. Multiple expected sources are alternatives, not additive credits.

**Fix:** Assert reciprocal rank from the first expected source found in retrieved order.

**Prevention:** For metric tests, write out `retrieved_source_ids`, `expected_source_ids`, and the first matching rank.

## 23. Local hashing vector model was mistaken for semantic embedding

**Symptom:** A test expected query text containing `emesis` to retrieve a chunk containing `vomiting` even without lexical overlap.

**Root cause:** `HashingEmbeddingModel` is a deterministic hashed token-vector baseline. It does not know synonyms unless overlap or hash collision creates similarity.

**Fix:** Updated the expectation to match the implemented model behavior and documented that the local vector baseline is vector plumbing, not true semantic retrieval.

**Prevention:** Do not call the local hashing baseline production semantic search. Add real semantic embeddings behind `EmbeddingModel` before claiming synonym behavior.

## 24. Comparison test assumed keyword must beat vector retrieval

**Symptom:** End-to-end comparison failed because local vector hit-rate exceeded keyword hit-rate on the current retrieval-question set.

**Root cause:** The test encoded a performance ordering assumption instead of verifying the comparison contract.

**Fix:** Asserted that both retrievers run and produce valid metric ranges, leaving the report to show which retriever performs better.

**Prevention:** On full corpus/eval tests, measure performance instead of asserting the desired winner. Use tiny controlled fixtures for deterministic ranking claims.

## 25. Top-k summary assertion expected a default instead of the caller value

**Symptom:** A comparison result called with `top_k=3` was asserted to contain `top_k=5`.

**Root cause:** The test expected the default value instead of the value passed by the caller.

**Fix:** Asserted the caller-supplied `top_k` value.

**Prevention:** Keep pass-through tests for caller-controlled evaluation settings.

## 26. Tie handling was lost in comparison notes

**Symptom:** A test expected only `embedding` as the best hit-rate retriever even though `embedding` and `hybrid` had equal hit_rate@k.

**Root cause:** The assertion assumed a single winner instead of preserving all tied best retrievers.

**Fix:** Return and assert all retrievers tied for the best metric value.

**Prevention:** Comparison reports should not collapse ties unless a deterministic tie-breaking rule is explicitly part of the contract.

## 27. Hybrid top-k propagation test expected the default instead of caller value

**Symptom:** A comparison result called with `top_k=3` was asserted to contain `top_k=5`.

**Root cause:** The test expected the default instead of the caller-supplied value.

**Fix:** Asserted that every summary preserves `result["top_k"]`.

**Prevention:** Pass-through tests should compare downstream values to the caller-provided value, not to defaults.

## 28. Hybrid scoring initially treated keyword score as a float-only value

**Symptom:** Type checking reported tuple/float mismatches in `HybridRetriever`.

**Root cause:** Existing `score_chunk(...)` returns both score and matched terms: `tuple[float, list[str]]`.

**Fix:** Unpacked `keyword_score, keyword_matched_terms` and combined keyword and vector matched terms for the final `SearchResult`.

**Prevention:** Reuse existing function contracts carefully when composing new retrieval strategies.

## 29. Hybrid candidate scoring returned inside the candidate loop

**Symptom:** Hybrid retrieval only considered the first eligible candidate.

**Root cause:** `return score_hybrid_candidates(...)` was indented inside the loop that builds candidates.

**Fix:** Moved the return after the loop so all candidates are collected before normalization and ranking.

**Prevention:** Ranking code should include tests where the best candidate is not first in input order.

## 30. Comparison report could imply quality claims without guardrails

**Symptom:** Keyword, vector, and hybrid metrics could be read as proof that a retriever is generally superior.

**Root cause:** The report measured local synthetic eval performance, but not production semantic quality.

**Fix:** Added qualitative notes and interpretation guardrails explaining that hashing vectors are local deterministic retrieval baselines, not production semantic search.

**Prevention:** Retrieval comparison artifacts should separate measured results from claims about general retrieval quality.

## Follow-up Lessons

- Do not stack new features on a failing compile or failing application context.
- Cross-language contracts need tests for request JSON, response JSON, error envelopes, process failures, and stdout discipline.
- Configuration tests must not hide production missing-bean problems.
- Retrieval expectations are contract fixtures.
- Safety-critical routing should prefer structured reviewer-confirmed facts.
- Retrieval metrics need explicit definitions before interpreting results.
- Local vector retrieval plumbing is not the same thing as production semantic retrieval.
- Comparison reports should measure retrievers, not justify a preferred result.
- Comparison reports should preserve metric ties instead of forcing a single winner.
- Hybrid retrieval must normalize component scores before weighted combination.
- Pass-through tests should assert caller-provided values, not defaults.
