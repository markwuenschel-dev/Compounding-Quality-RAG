# Generated File Review Queue

This is the running list of files supplied without a request to seed bugs.

The purpose is to revisit generated code after the demo and perform a slower manual review. Files that were explicitly supplied as bug-seeded exercises are excluded. When a corrected, non-seeded replacement was later supplied, the corrected path is included.

## Current readiness and resilience batch

- [ ] `services/review-api/src/main/java/com/compoundingquality/reviewapi/api/ReadinessController.java`
- [ ] `services/review-api/src/main/java/com/compoundingquality/reviewapi/application/ReadinessService.java`
- [ ] `services/review-api/src/main/java/com/compoundingquality/reviewapi/application/PythonCommandProbe.java`
- [ ] `services/review-api/src/main/java/com/compoundingquality/reviewapi/application/DefaultPythonCommandProbe.java`
- [ ] `services/review-api/src/main/java/com/compoundingquality/reviewapi/dto/ReadinessResponse.java`
- [ ] `services/review-api/src/test/java/com/compoundingquality/reviewapi/api/ReadinessControllerTest.java`
- [ ] `services/review-api/src/test/java/com/compoundingquality/reviewapi/application/ReadinessServiceTest.java`
- [ ] `apps/review-ui/src/api/types.ts`
- [ ] `apps/review-ui/src/api/reviewApi.ts`
- [ ] `apps/review-ui/src/api/reviewApi.test.ts`
- [ ] `apps/review-ui/src/hooks/useBackendReadiness.ts`
- [ ] `apps/review-ui/src/components/BackendStatus.tsx`
- [ ] `apps/review-ui/src/components/BackendStatus.test.tsx`
- [ ] `apps/review-ui/src/components/ConcernInputForm.tsx`
- [ ] `apps/review-ui/src/components/ReviewSummaryForm.tsx`
- [ ] `apps/review-ui/src/App.tsx`
- [ ] `apps/review-ui/src/App.readiness.test.tsx`
- [ ] `apps/review-ui/src/readiness.css`
- [ ] `docs/generated_file_review_queue.md`

## Earlier non-seeded files supplied in this conversation

### Repository and demo documentation

- [ ] `README.md`
- [ ] `docs/architecture.md`
- [ ] `docs/browser_demo_script.md`

### React application setup and API boundary

- [ ] `apps/review-ui/package.json`
- [ ] `apps/review-ui/tsconfig.json`
- [ ] `apps/review-ui/vite.config.ts`
- [ ] `apps/review-ui/index.html`
- [ ] `apps/review-ui/src/main.tsx`
- [ ] `apps/review-ui/src/styles.css`
- [ ] `apps/review-ui/src/api/types.ts`
- [ ] `apps/review-ui/src/api/reviewApi.ts`

### Demo-polish components

- [ ] `apps/review-ui/src/components/WorkflowProgress.tsx`
- [ ] `apps/review-ui/src/components/ConcernInputForm.tsx`
- [ ] `apps/review-ui/src/components/ChecklistPanel.tsx`
- [ ] `apps/review-ui/src/components/ReviewSummaryForm.tsx`
- [ ] `apps/review-ui/src/components/FinalAssessmentPanel.tsx`

### Demo operator tools

- [ ] `apps/review-ui/src/demo/demoCases.ts`
- [ ] `apps/review-ui/src/components/DemoToolbar.tsx`
- [ ] `apps/review-ui/src/components/DemoToolbar.test.tsx`
- [ ] `apps/review-ui/src/utils/assessmentSummary.ts`
- [ ] `apps/review-ui/src/utils/assessmentSummary.test.ts`
- [ ] `apps/review-ui/src/components/FinalAssessmentPanel.test.tsx`
- [ ] `apps/review-ui/src/demoControls.css`

### Corrected non-seeded test replacements

- [ ] `apps/review-ui/src/App.test.tsx`
- [ ] `apps/review-ui/src/components/FinalAssessmentPanel.test.tsx`

## Review order after the demo

1. Runtime behavior and error classification
2. State reset and retry correctness
3. Accessibility and semantic queries
4. Java/Python HTTP boundary behavior
5. Duplication and component boundaries
6. Test brittleness and timing behavior
7. Documentation accuracy

## Narrative extraction MLE batch

- [ ] `rag-engine-python/app/schemas.py`
- [ ] `rag-engine-python/app/contextual_missing_information.py`
- [ ] `rag-engine-python/app/review_summary_extraction.py`
- [ ] `rag-engine-python/app/review_summary_evaluate.py`
- [ ] `rag-engine-python/app/api_runner.py`
- [ ] `rag-engine-python/data/eval/review_summary_extraction_cases.json`
- [ ] `rag-engine-python/tests/test_contextual_missing_information.py`
- [ ] `rag-engine-python/tests/test_review_summary_extraction.py`
- [ ] `rag-engine-python/tests/test_api_runner_review_summary_extraction.py`
- [ ] `rag-engine-python/tests/test_review_summary_evaluate.py`
- [ ] `rag-engine-python/reports/review_summary_extraction_evaluation.md`

## Narrative extraction evaluation-fix batch

- [ ] `rag-engine-python/app/review_summary_extraction.py`
- [ ] `rag-engine-python/app/contextual_missing_information.py`
- [ ] `rag-engine-python/app/review_summary_evaluate.py`
- [ ] `rag-engine-python/tests/test_review_summary_extraction.py`
- [ ] `rag-engine-python/tests/test_contextual_missing_information.py`
- [ ] `rag-engine-python/tests/test_review_summary_evaluate.py`

## Full-stack narrative extraction integration

- [ ] `services/review-api/src/main/java/com/compoundingquality/reviewapi/api/ReviewSummaryExtractionController.java`
- [ ] `services/review-api/src/main/java/com/compoundingquality/reviewapi/application/ReviewSummaryExtractionService.java`
- [ ] `services/review-api/src/main/java/com/compoundingquality/reviewapi/dto/ReviewSummaryExtractRequest.java`
- [ ] `services/review-api/src/main/java/com/compoundingquality/reviewapi/dto/ReviewSummaryExtractResponse.java`
- [ ] `services/review-api/src/main/java/com/compoundingquality/reviewapi/error/GlobalExceptionHandler.java`
- [ ] `services/review-api/src/main/java/com/compoundingquality/reviewapi/rag/RagEngineClient.java`
- [ ] `services/review-api/src/main/java/com/compoundingquality/reviewapi/rag/RagReviewSummaryExtractRequest.java`
- [ ] `services/review-api/src/main/java/com/compoundingquality/reviewapi/rag/RagReviewSummaryExtractResult.java`
- [ ] `services/review-api/src/main/java/com/compoundingquality/reviewapi/rag/PythonProcessRagEngineClient.java`
- [ ] `services/review-api/src/test/java/com/compoundingquality/reviewapi/api/ReviewSummaryExtractionControllerTest.java`
- [ ] `services/review-api/src/test/java/com/compoundingquality/reviewapi/application/ReviewSummaryExtractionServiceTest.java`
- [ ] `apps/review-ui/src/api/types.ts`
- [ ] `apps/review-ui/src/api/reviewApi.ts`
- [ ] `apps/review-ui/src/api/reviewApi.test.ts`
- [ ] `apps/review-ui/src/components/InvestigationNotesForm.tsx`
- [ ] `apps/review-ui/src/components/InvestigationNotesForm.test.tsx`
- [ ] `apps/review-ui/src/components/ExtractedFindingsPanel.tsx`
- [ ] `apps/review-ui/src/components/ExtractedFindingsPanel.test.tsx`
- [ ] `apps/review-ui/src/components/ReviewSummaryForm.tsx`
- [ ] `apps/review-ui/src/components/ReviewSummaryForm.test.tsx`
- [ ] `apps/review-ui/src/demo/demoCases.ts`
- [ ] `apps/review-ui/src/App.tsx`
- [ ] `apps/review-ui/src/App.test.tsx`
- [ ] `apps/review-ui/src/App.readiness.test.tsx`
- [ ] `apps/review-ui/src/extraction.css`
- [ ] `docs/generated_file_review_queue.md`

## Unseen holdout evaluation scaffold

- [ ] `rag-engine-python/app/holdout_evaluate.py`
- [ ] `rag-engine-python/data/eval/review_summary_extraction_holdout.json`
- [ ] `rag-engine-python/data/eval/retrieval_questions_holdout.json`
- [ ] `rag-engine-python/tests/test_holdout_evaluate.py`
- [ ] `docs/evaluation_case_authoring.md`
- [ ] `docs/holdout_case_capture_worksheet.md`
- [ ] `docs/generated_file_review_queue.md`


## Reference and reported-trigger policy batch

- [ ] `rag-engine-python/app/schemas.py`
- [ ] `rag-engine-python/app/review_summary_extraction.py`
- [ ] `rag-engine-python/app/contextual_missing_information.py`
- [ ] `apps/review-ui/src/components/ReviewSummaryForm.tsx`
- [ ] `rag-engine-python/tests/test_reference_and_trigger_policy.py`
- [ ] `rag-engine-python/tests/test_contextual_question_boundaries.py`
- [ ] `apps/review-ui/src/components/ReviewSummaryForm.reference.test.tsx`
- [ ] `docs/reference_review_labeling_policy.md`
- [ ] `docs/reported_trigger_and_clinical_context_policy.md`

## Review-scope defaults batch

- [ ] `rag-engine-python/app/review_summary_policy.py`
- [ ] `rag-engine-python/app/review_summary_extraction.py`
- [ ] `rag-engine-python/app/contextual_missing_information.py`
- [ ] `rag-engine-python/tests/test_review_summary_policy.py`
- [ ] `rag-engine-python/tests/test_contextual_missing_information_regressions.py`
- [ ] `rag-engine-python/data/eval/review_summary_extraction_development.json`
- [ ] `docs/review_summary_default_policy.md`
