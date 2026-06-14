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
- [ ] `apps/review-ui/vite.config.ts`
- [ ] `apps/review-ui/src/test/setup.ts`
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
4. Java/Python process-boundary behavior
5. Duplication and component boundaries
6. Test brittleness and timing behavior
7. Documentation accuracy
