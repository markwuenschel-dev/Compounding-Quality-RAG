import { useMemo, useState } from "react";
import {
  createChecklist,
  createFinalAssessment,
  getReviewApiErrorMessage,
  ReviewApiError,
} from "./api/reviewApi";
import type {
  ChecklistResponse,
  FinalAssessmentResponse,
  ReviewSummaryRequest,
} from "./api/types";
import { BackendStatus } from "./components/BackendStatus";
import { ChecklistPanel } from "./components/ChecklistPanel";
import { ConcernInputForm } from "./components/ConcernInputForm";
import { DemoToolbar } from "./components/DemoToolbar";
import { FinalAssessmentPanel } from "./components/FinalAssessmentPanel";
import { ReviewSummaryForm } from "./components/ReviewSummaryForm";
import { WorkflowProgress } from "./components/WorkflowProgress";
import {
  DEFAULT_DEMO_CASE_ID,
  getDemoCase,
  type DemoCaseId,
} from "./demo/demoCases";
import { useBackendReadiness } from "./hooks/useBackendReadiness";
import "./demoControls.css";
import "./readiness.css";

type WorkflowError = {
  message: string;
  retryable: boolean;
};

type ChecklistState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; checklist: ChecklistResponse }
  | { status: "error"; error: WorkflowError };

type FinalAssessmentState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; assessment: FinalAssessmentResponse }
  | { status: "error"; error: WorkflowError };

export function App() {
  const readiness = useBackendReadiness();
  const backendReady = readiness.status === "ready";

  const [selectedDemoCaseId, setSelectedDemoCaseId] =
    useState<DemoCaseId>(DEFAULT_DEMO_CASE_ID);
  const [workflowVersion, setWorkflowVersion] = useState(0);
  const [concernSeed, setConcernSeed] = useState("");
  const [draftConcernText, setDraftConcernText] = useState("");
  const [reviewSummarySeed, setReviewSummarySeed] =
    useState<ReviewSummaryRequest>();
  const [submittedConcernText, setSubmittedConcernText] =
    useState("");
  const [lastReviewSummary, setLastReviewSummary] =
    useState<ReviewSummaryRequest>();
  const [checklistState, setChecklistState] =
    useState<ChecklistState>({ status: "idle" });
  const [finalAssessmentState, setFinalAssessmentState] =
    useState<FinalAssessmentState>({ status: "idle" });

  const canStartOver = useMemo(
    () =>
      draftConcernText.trim().length > 0 ||
      checklistState.status !== "idle" ||
      finalAssessmentState.status !== "idle",
    [
      draftConcernText,
      checklistState.status,
      finalAssessmentState.status,
    ],
  );

  function handleLoadDemoCase() {
    const demoCase = getDemoCase(selectedDemoCaseId);

    setConcernSeed(demoCase.concernText);
    setDraftConcernText(demoCase.concernText);
    setReviewSummarySeed(demoCase.reviewSummary);
    setSubmittedConcernText("");
    setLastReviewSummary(undefined);
    setChecklistState({ status: "idle" });
    setFinalAssessmentState({ status: "idle" });
    setWorkflowVersion((version) => version + 1);
  }

  function handleStartOver() {
    setSelectedDemoCaseId(DEFAULT_DEMO_CASE_ID);
    setConcernSeed("");
    setDraftConcernText("");
    setReviewSummarySeed(undefined);
    setSubmittedConcernText("");
    setLastReviewSummary(undefined);
    setChecklistState({ status: "idle" });
    setFinalAssessmentState({ status: "idle" });
    setWorkflowVersion((version) => version + 1);
  }

  async function handleChecklistSubmit(concernText: string) {
    if (!backendReady) {
      return;
    }

    setSubmittedConcernText(concernText);
    setChecklistState({ status: "loading" });
    setFinalAssessmentState({ status: "idle" });

    try {
      const checklist = await createChecklist({ concernText });
      setChecklistState({ status: "success", checklist });
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

  async function handleFinalAssessmentSubmit(
    reviewSummary: ReviewSummaryRequest,
  ) {
    if (!backendReady) {
      return;
    }

    setLastReviewSummary(reviewSummary);
    setFinalAssessmentState({ status: "loading" });

    try {
      const assessment = await createFinalAssessment({
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
          <div className="brand-mark" aria-hidden="true">
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
              Turn a synthetic concern narrative into a
              grounded checklist, capture reviewer findings,
              and produce a structured final assessment
              without hiding the evidence or review boundary.
            </p>
          </div>
        </section>

        <BackendStatus readiness={readiness} />

        <WorkflowProgress
          checklistStatus={checklistState.status}
          finalAssessmentStatus={finalAssessmentState.status}
        />

        <div className="content-grid">
          <section
            className="workflow-column"
            aria-label="Review workflow"
          >
            <DemoToolbar
              selectedDemoCaseId={selectedDemoCaseId}
              onSelectedDemoCaseChange={setSelectedDemoCaseId}
              onLoadDemoCase={handleLoadDemoCase}
              onStartOver={handleStartOver}
              canStartOver={canStartOver}
            />

            <ConcernInputForm
              key={`concern-${workflowVersion}`}
              isSubmitting={checklistState.status === "loading"}
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
              <div
                className="status-banner status-loading"
                role="status"
              >
                <span
                  className="spinner"
                  aria-hidden="true"
                />
                Generating checklist...
              </div>
            ) : null}

            {checklistState.status === "error" ? (
              <div
                className="status-banner status-error"
                role="alert"
              >
                <span>{checklistState.error.message}</span>
                {checklistState.error.retryable ? (
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={handleRetryChecklist}
                    disabled={!backendReady}
                  >
                    Retry checklist
                  </button>
                ) : null}
              </div>
            ) : null}

            {checklistState.status === "success" ? (
              <>
                <ChecklistPanel
                  checklist={checklistState.checklist}
                />

                <ReviewSummaryForm
                  key={`review-${workflowVersion}`}
                  isSubmitting={
                    finalAssessmentState.status === "loading"
                  }
                  isSubmissionDisabled={!backendReady}
                  onSubmit={handleFinalAssessmentSubmit}
                  initialValues={reviewSummarySeed}
                />

                {finalAssessmentState.status === "loading" ? (
                  <div
                    className="status-banner status-loading"
                    role="status"
                  >
                    <span
                      className="spinner"
                      aria-hidden="true"
                    />
                    Generating final assessment...
                  </div>
                ) : null}

                {finalAssessmentState.status === "error" ? (
                  <div
                    className="status-banner status-error"
                    role="alert"
                  >
                    <span>
                      {finalAssessmentState.error.message}
                    </span>
                    {finalAssessmentState.error.retryable ? (
                      <button
                        className="ghost-button"
                        type="button"
                        onClick={handleRetryFinalAssessment}
                        disabled={!backendReady}
                      >
                        Retry final assessment
                      </button>
                    ) : null}
                  </div>
                ) : null}

                {finalAssessmentState.status === "success" ? (
                  <FinalAssessmentPanel
                    assessment={
                      finalAssessmentState.assessment
                    }
                  />
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
                <li>Evidence supports the checklist.</li>
                <li>
                  Reviewer findings drive final routing.
                </li>
                <li>
                  Unsupported record-access requests are
                  refused.
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
        Synthetic learning artifact · Not production policy or
        clinical advice
      </footer>
    </div>
  );
}

function toWorkflowError(
  error: unknown,
  fallbackMessage: string,
): WorkflowError {
  if (error instanceof ReviewApiError) {
    return {
      message: getReviewApiErrorMessage(error, fallbackMessage),
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
