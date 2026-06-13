import { useState } from "react";
import {
  createChecklist,
  createFinalAssessment,
  ReviewApiError,
} from "./api/reviewApi";
import type {
  ChecklistResponse,
  FinalAssessmentResponse,
  ReviewSummaryRequest,
} from "./api/types";
import { ChecklistPanel } from "./components/ChecklistPanel";
import { ConcernInputForm } from "./components/ConcernInputForm";
import { FinalAssessmentPanel } from "./components/FinalAssessmentPanel";
import { ReviewSummaryForm } from "./components/ReviewSummaryForm";
import { WorkflowProgress } from "./components/WorkflowProgress";

type ChecklistState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; checklist: ChecklistResponse }
  | { status: "error"; message: string };

type FinalAssessmentState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; assessment: FinalAssessmentResponse }
  | { status: "error"; message: string };

export function App() {
  const [submittedConcernText, setSubmittedConcernText] = useState("");
  const [checklistState, setChecklistState] = useState<ChecklistState>({
    status: "idle",
  });
  const [finalAssessmentState, setFinalAssessmentState] =
    useState<FinalAssessmentState>({ status: "idle" });

  async function handleChecklistSubmit(concernText: string) {
    setSubmittedConcernText(concernText);
    setChecklistState({ status: "loading" });
    setFinalAssessmentState({ status: "idle" });

    try {
      const checklist = await createChecklist({ concernText });
      setChecklistState({ status: "success", checklist });
    } catch (error) {
      setChecklistState({
        status: "error",
        message: getWorkflowErrorMessage(error, "Unable to generate checklist."),
      });
    }
  }

  async function handleFinalAssessmentSubmit(
    reviewSummary: ReviewSummaryRequest,
  ) {
    setFinalAssessmentState({ status: "loading" });

    try {
      const assessment = await createFinalAssessment({
        concernText: submittedConcernText,
        topK: 3,
        reviewSummary,
      });

      setFinalAssessmentState({ status: "success", assessment });
    } catch (error) {
      setFinalAssessmentState({
        status: "error",
        message: getWorkflowErrorMessage(
          error,
          "Unable to generate final assessment.",
        ),
      });
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">
            CQ
          </div>
          <div>
            <p className="brand-name">Compounding Quality</p>
            <p className="brand-subtitle">Review Support Workbench</p>
          </div>
        </div>
        <span className="environment-pill">Synthetic demo</span>
      </header>

      <main className="page-shell">
        <section className="hero">
          <div>
            <p className="eyebrow">Human-in-the-loop workflow</p>
            <h1>Compounding Quality Review</h1>
            <p className="hero-copy">
              Turn a synthetic concern narrative into a grounded checklist,
              capture reviewer findings, and produce a structured final
              assessment without hiding the evidence or review boundary.
            </p>
          </div>
        </section>

        <WorkflowProgress
          checklistStatus={checklistState.status}
          finalAssessmentStatus={finalAssessmentState.status}
        />

        <div className="content-grid">
          <section className="workflow-column" aria-label="Review workflow">
            <ConcernInputForm
              isSubmitting={checklistState.status === "loading"}
              onSubmit={handleChecklistSubmit}
            />

            {checklistState.status === "idle" ? (
              <div className="status-banner status-neutral">
                No checklist generated yet.
              </div>
            ) : null}

            {checklistState.status === "loading" ? (
              <div className="status-banner status-loading" role="status">
                <span className="spinner" aria-hidden="true" />
                Generating checklist...
              </div>
            ) : null}

            {checklistState.status === "error" ? (
              <div className="status-banner status-error" role="alert">
                {checklistState.message}
              </div>
            ) : null}

            {checklistState.status === "success" ? (
              <>
                <ChecklistPanel checklist={checklistState.checklist} />

                <ReviewSummaryForm
                  isSubmitting={finalAssessmentState.status === "loading"}
                  onSubmit={handleFinalAssessmentSubmit}
                />

                {finalAssessmentState.status === "loading" ? (
                  <div className="status-banner status-loading" role="status">
                    <span className="spinner" aria-hidden="true" />
                    Generating final assessment...
                  </div>
                ) : null}

                {finalAssessmentState.status === "error" ? (
                  <div className="status-banner status-error" role="alert">
                    {finalAssessmentState.message}
                  </div>
                ) : null}

                {finalAssessmentState.status === "success" ? (
                  <FinalAssessmentPanel
                    assessment={finalAssessmentState.assessment}
                  />
                ) : null}
              </>
            ) : null}
          </section>

          <aside className="sidebar" aria-label="Demo context">
            <section className="card sidebar-card">
              <p className="eyebrow">Demo boundary</p>
              <h2>Synthetic data only</h2>
              <p>
                This public workbench does not access real customer records,
                prescriptions, compounding records, inventory systems, or
                licensed drug-information sources.
              </p>
            </section>

            <section className="card sidebar-card">
              <p className="eyebrow">Workflow ownership</p>
              <h2>Human review stays central</h2>
              <ul className="sidebar-list">
                <li>Evidence supports the checklist.</li>
                <li>Reviewer findings drive final routing.</li>
                <li>Unsupported record-access requests are refused.</li>
                <li>The final decision remains with the pharmacist reviewer.</li>
              </ul>
            </section>

            <section className="card sidebar-card accent-card">
              <p className="eyebrow">Current retrieval path</p>
              <h2>Keyword retrieval</h2>
              <p>
                Keyword retrieval remains the default application path.
                Embedding and hybrid retrieval remain evaluation baselines.
              </p>
            </section>
          </aside>
        </div>
      </main>

      <footer className="footer">
        Synthetic learning artifact · Not production policy or clinical advice
      </footer>
    </div>
  );
}

function getWorkflowErrorMessage(error: unknown, fallbackMessage: string): string {
  if (error instanceof ReviewApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallbackMessage;
}
