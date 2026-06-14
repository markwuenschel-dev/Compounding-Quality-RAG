import { useMemo, useState } from "react";
import {
  createChecklist,
  createFinalAssessment,
  extractReviewSummary,
  getReviewApiErrorMessage,
  ReviewApiError,
} from "./api/reviewApi";
import type {
  ChecklistResponse,
  FinalAssessmentResponse,
  ReviewSummaryExtractResponse,
  ReviewSummaryRequest,
} from "./api/types";
import { BackendStatus } from "./components/BackendStatus";
import { ChecklistPanel } from "./components/ChecklistPanel";
import { ConcernInputForm } from "./components/ConcernInputForm";
import { DemoToolbar } from "./components/DemoToolbar";
import { ExtractedFindingsPanel } from "./components/ExtractedFindingsPanel";
import { FinalAssessmentPanel } from "./components/FinalAssessmentPanel";
import { InvestigationNotesForm } from "./components/InvestigationNotesForm";
import { ReviewSummaryForm } from "./components/ReviewSummaryForm";
import { WorkflowProgress } from "./components/WorkflowProgress";
import {
  DEFAULT_DEMO_CASE_ID,
  getDemoCase,
  type DemoCaseId,
} from "./demo/demoCases";
import { useBackendReadiness } from "./hooks/useBackendReadiness";
import "./demoControls.css";
import "./extraction.css";
import "./readiness.css";

type WorkflowError = {
  message: string;
  retryable: boolean;
};

type ChecklistState =
  | { status: "idle" }
  | { status: "loading" }
  | {
      status: "success";
      checklist: ChecklistResponse;
    }
  | { status: "error"; error: WorkflowError };

type ExtractionState =
  | { status: "idle" }
  | { status: "loading" }
  | {
      status: "success";
      extraction: ReviewSummaryExtractResponse;
    }
  | { status: "error"; error: WorkflowError };

type FinalAssessmentState =
  | { status: "idle" }
  | { status: "loading" }
  | {
      status: "success";
      assessment: FinalAssessmentResponse;
    }
  | { status: "error"; error: WorkflowError };

export function App() {
  const readiness = useBackendReadiness();
  const backendReady = readiness.status === "ready";

  const [
    selectedDemoCaseId,
    setSelectedDemoCaseId,
  ] = useState<DemoCaseId>(DEFAULT_DEMO_CASE_ID);
  const [workflowVersion, setWorkflowVersion] =
    useState(0);
  const [extractionVersion, setExtractionVersion] =
    useState(0);
  const [concernSeed, setConcernSeed] = useState("");
  const [draftConcernText, setDraftConcernText] =
    useState("");
  const [
    pharmacistNotesSeed,
    setPharmacistNotesSeed,
  ] = useState("");
  const [
    draftPharmacistNotes,
    setDraftPharmacistNotes,
  ] = useState("");
  const [
    lastExtractedNotes,
    setLastExtractedNotes,
  ] = useState("");
  const [
    submittedConcernText,
    setSubmittedConcernText,
  ] = useState("");
  const [
    lastReviewSummary,
    setLastReviewSummary,
  ] = useState<ReviewSummaryRequest>();
  const [checklistState, setChecklistState] =
    useState<ChecklistState>({ status: "idle" });
  const [extractionState, setExtractionState] =
    useState<ExtractionState>({ status: "idle" });
  const [
    finalAssessmentState,
    setFinalAssessmentState,
  ] = useState<FinalAssessmentState>({
    status: "idle",
  });

  const canStartOver = useMemo(
    () =>
      draftConcernText.trim().length > 0 ||
      draftPharmacistNotes.trim().length > 0 ||
      checklistState.status !== "idle" ||
      extractionState.status !== "idle" ||
      finalAssessmentState.status !== "idle",
    [
      draftConcernText,
      draftPharmacistNotes,
      checklistState.status,
      extractionState.status,
      finalAssessmentState.status,
    ],
  );

  function handleLoadDemoCase() {
    const demoCase = getDemoCase(selectedDemoCaseId);
    const notes = demoCase.pharmacistNotes ?? "";

    setConcernSeed(demoCase.concernText);
    setDraftConcernText(demoCase.concernText);
    setPharmacistNotesSeed(notes);
    setDraftPharmacistNotes(notes);
    setLastExtractedNotes("");
    setSubmittedConcernText("");
    setLastReviewSummary(undefined);
    setChecklistState({ status: "idle" });
    setExtractionState({ status: "idle" });
    setFinalAssessmentState({ status: "idle" });
    setWorkflowVersion((version) => version + 1);
  }

  function handleStartOver() {
    setSelectedDemoCaseId(DEFAULT_DEMO_CASE_ID);
    setConcernSeed("");
    setDraftConcernText("");
    setPharmacistNotesSeed("");
    setDraftPharmacistNotes("");
    setLastExtractedNotes("");
    setSubmittedConcernText("");
    setLastReviewSummary(undefined);
    setChecklistState({ status: "idle" });
    setExtractionState({ status: "idle" });
    setFinalAssessmentState({ status: "idle" });
    setWorkflowVersion((version) => version + 1);
  }

  function handlePharmacistNotesChange(notes: string) {
    setDraftPharmacistNotes(notes);

    if (
      extractionState.status === "success" &&
      notes.trim() !== lastExtractedNotes
    ) {
      setExtractionState({ status: "idle" });
      setLastReviewSummary(undefined);
      setFinalAssessmentState({ status: "idle" });
    }
  }

  async function handleChecklistSubmit(
    concernText: string,
  ) {
    if (!backendReady) {
      return;
    }

    setSubmittedConcernText(concernText);
    setChecklistState({ status: "loading" });
    setExtractionState({ status: "idle" });
    setFinalAssessmentState({ status: "idle" });

    try {
      const checklist = await createChecklist({
        concernText,
      });
      setChecklistState({
        status: "success",
        checklist,
      });
    } catch (error) {
      setChecklistState({
        status: "error",
        error: toWorkflowError(
          error,
          "Unable to generate checklist.",
        ),
      });
    }
  }

  async function handleExtractionSubmit(
    pharmacistNotes: string,
  ) {
    if (!backendReady) {
      return;
    }

    setDraftPharmacistNotes(pharmacistNotes);
    setLastExtractedNotes(pharmacistNotes);
    setExtractionState({ status: "loading" });
    setFinalAssessmentState({ status: "idle" });
    setLastReviewSummary(undefined);

    try {
      const extraction = await extractReviewSummary({
        concernText: submittedConcernText,
        pharmacistNotes,
      });

      setExtractionState({
        status: "success",
        extraction,
      });
      setExtractionVersion((version) => version + 1);
    } catch (error) {
      setExtractionState({
        status: "error",
        error: toWorkflowError(
          error,
          "Unable to extract reviewer findings.",
        ),
      });
    }
  }

  async function handleFinalAssessmentSubmit(
    reviewSummary: ReviewSummaryRequest,
  ) {
    if (!backendReady) {
      return;
    }

    setLastReviewSummary(reviewSummary);
    setFinalAssessmentState({ status: "loading" });

    try {
      const assessment =
        await createFinalAssessment({
          concernText: submittedConcernText,
          topK: 3,
          reviewSummary,
        });

      setFinalAssessmentState({
        status: "success",
        assessment,
      });
    } catch (error) {
      setFinalAssessmentState({
        status: "error",
        error: toWorkflowError(
          error,
          "Unable to generate final assessment.",
        ),
      });
    }
  }

  function handleRetryChecklist() {
    if (
      submittedConcernText.length === 0 ||
      !backendReady
    ) {
      return;
    }

    void handleChecklistSubmit(submittedConcernText);
  }

  function handleRetryExtraction() {
    if (
      lastExtractedNotes.length === 0 ||
      !backendReady
    ) {
      return;
    }

    void handleExtractionSubmit(lastExtractedNotes);
  }

  function handleRetryFinalAssessment() {
    if (!lastReviewSummary || !backendReady) {
      return;
    }

    void handleFinalAssessmentSubmit(lastReviewSummary);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div
            className="brand-mark"
            aria-hidden="true"
          >
            CQ
          </div>
          <div>
            <p className="brand-name">
              Compounding Quality
            </p>
            <p className="brand-subtitle">
              Review Support Workbench
            </p>
          </div>
        </div>
        <span className="environment-pill">
          Synthetic demo
        </span>
      </header>

      <main className="page-shell">
        <section className="hero">
          <div>
            <p className="eyebrow">
              Human-in-the-loop workflow
            </p>
            <h1>Compounding Quality Review</h1>
            <p className="hero-copy">
              Turn customer and pharmacist narratives into a
              grounded checklist, reviewable structured
              findings, and a final assessment without hiding
              evidence or uncertainty.
            </p>
          </div>
        </section>

        <BackendStatus readiness={readiness} />

        <WorkflowProgress
          checklistStatus={checklistState.status}
          finalAssessmentStatus={
            finalAssessmentState.status
          }
        />

        <div className="content-grid">
          <section
            className="workflow-column"
            aria-label="Review workflow"
          >
            <DemoToolbar
              selectedDemoCaseId={selectedDemoCaseId}
              onSelectedDemoCaseChange={
                setSelectedDemoCaseId
              }
              onLoadDemoCase={handleLoadDemoCase}
              onStartOver={handleStartOver}
              canStartOver={canStartOver}
            />

            <ConcernInputForm
              key={`concern-${workflowVersion}`}
              isSubmitting={
                checklistState.status === "loading"
              }
              isSubmissionDisabled={!backendReady}
              onSubmit={handleChecklistSubmit}
              initialConcernText={concernSeed}
              onConcernTextChange={setDraftConcernText}
            />

            {checklistState.status === "idle" ? (
              <div className="status-banner status-neutral">
                No checklist generated yet.
              </div>
            ) : null}

            {checklistState.status === "loading" ? (
              <LoadingBanner text="Generating checklist..." />
            ) : null}

            {checklistState.status === "error" ? (
              <ErrorBanner
                error={checklistState.error}
                retryLabel="Retry checklist"
                onRetry={handleRetryChecklist}
                retryDisabled={!backendReady}
              />
            ) : null}

            {checklistState.status === "success" ? (
              <>
                <ChecklistPanel
                  checklist={checklistState.checklist}
                />

                <InvestigationNotesForm
                  key={`notes-${workflowVersion}`}
                  initialNotes={pharmacistNotesSeed}
                  isSubmitting={
                    extractionState.status === "loading"
                  }
                  isSubmissionDisabled={!backendReady}
                  onNotesChange={
                    handlePharmacistNotesChange
                  }
                  onSubmit={handleExtractionSubmit}
                />

                {extractionState.status === "loading" ? (
                  <LoadingBanner text="Extracting reviewer findings..." />
                ) : null}

                {extractionState.status === "error" ? (
                  <ErrorBanner
                    error={extractionState.error}
                    retryLabel="Retry extraction"
                    onRetry={handleRetryExtraction}
                    retryDisabled={!backendReady}
                  />
                ) : null}

                {extractionState.status === "success" ? (
                  <>
                    <ExtractedFindingsPanel
                      extraction={
                        extractionState.extraction
                      }
                    />

                    <ReviewSummaryForm
                      key={`review-${workflowVersion}-${extractionVersion}`}
                      isSubmitting={
                        finalAssessmentState.status ===
                        "loading"
                      }
                      isSubmissionDisabled={!backendReady}
                      onSubmit={
                        handleFinalAssessmentSubmit
                      }
                      initialValues={
                        extractionState.extraction
                          .reviewSummary
                      }
                    />

                    {finalAssessmentState.status ===
                    "loading" ? (
                      <LoadingBanner text="Generating final assessment..." />
                    ) : null}

                    {finalAssessmentState.status ===
                    "error" ? (
                      <ErrorBanner
                        error={
                          finalAssessmentState.error
                        }
                        retryLabel="Retry final assessment"
                        onRetry={
                          handleRetryFinalAssessment
                        }
                        retryDisabled={!backendReady}
                      />
                    ) : null}

                    {finalAssessmentState.status ===
                    "success" ? (
                      <FinalAssessmentPanel
                        assessment={
                          finalAssessmentState.assessment
                        }
                      />
                    ) : null}
                  </>
                ) : null}
              </>
            ) : null}
          </section>

          <aside
            className="sidebar"
            aria-label="Demo context"
          >
            <section className="card sidebar-card">
              <p className="eyebrow">Demo boundary</p>
              <h2>Synthetic data only</h2>
              <p>
                This public workbench does not access real
                customer records, prescriptions, compounding
                records, inventory systems, or licensed
                drug-information sources.
              </p>
            </section>

            <section className="card sidebar-card">
              <p className="eyebrow">
                Workflow ownership
              </p>
              <h2>Human review stays central</h2>
              <ul className="sidebar-list">
                <li>
                  The model extracts; deterministic rules
                  ground the result.
                </li>
                <li>
                  The pharmacist confirms or corrects every
                  structured finding.
                </li>
                <li>
                  Structured severe triggers drive
                  escalation.
                </li>
                <li>
                  The final decision remains with the
                  pharmacist reviewer.
                </li>
              </ul>
            </section>

            <section className="card sidebar-card accent-card">
              <p className="eyebrow">
                Current retrieval path
              </p>
              <h2>Keyword retrieval</h2>
              <p>
                Keyword retrieval remains the default
                application path. Embedding and hybrid
                retrieval remain evaluation baselines.
              </p>
            </section>
          </aside>
        </div>
      </main>

      <footer className="footer">
        Synthetic learning artifact · Not production policy
        or clinical advice
      </footer>
    </div>
  );
}

function LoadingBanner({ text }: { text: string }) {
  return (
    <div
      className="status-banner status-loading"
      role="status"
    >
      <span
        className="spinner"
        aria-hidden="true"
      />
      {text}
    </div>
  );
}

function ErrorBanner({
  error,
  retryLabel,
  onRetry,
  retryDisabled,
}: {
  error: WorkflowError;
  retryLabel: string;
  onRetry: () => void;
  retryDisabled: boolean;
}) {
  return (
    <div
      className="status-banner status-error"
      role="alert"
    >
      <span>{error.message}</span>
      {error.retryable ? (
        <button
          className="ghost-button"
          type="button"
          onClick={onRetry}
          disabled={retryDisabled}
        >
          {retryLabel}
        </button>
      ) : null}
    </div>
  );
}

function toWorkflowError(
  error: unknown,
  fallbackMessage: string,
): WorkflowError {
  if (error instanceof ReviewApiError) {
    return {
      message: getReviewApiErrorMessage(
        error,
        fallbackMessage,
      ),
      retryable: error.retryable,
    };
  }

  if (error instanceof Error) {
    return {
      message: error.message,
      retryable: false,
    };
  }

  return {
    message: fallbackMessage,
    retryable: false,
  };
}
