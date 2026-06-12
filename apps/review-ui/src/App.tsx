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
    <main>
      <h1>Compounding Quality Review</h1>
      <p>
        Enter a synthetic concern narrative to generate a review-support
        checklist, then summarize reviewer findings to produce a final
        assessment.
      </p>

      <ConcernInputForm
        isSubmitting={checklistState.status === "loading"}
        onSubmit={handleChecklistSubmit}
      />

      {checklistState.status === "idle" ? (
        <p>No checklist generated yet.</p>
      ) : null}

      {checklistState.status === "loading" ? (
        <p role="status">Generating checklist...</p>
      ) : null}

      {checklistState.status === "error" ? (
        <p role="alert">{checklistState.message}</p>
      ) : null}

      {checklistState.status === "success" ? (
        <>
          <ChecklistPanel checklist={checklistState.checklist} />

          <ReviewSummaryForm
            isSubmitting={finalAssessmentState.status === "loading"}
            onSubmit={handleFinalAssessmentSubmit}
          />

          {finalAssessmentState.status === "loading" ? (
            <p role="status">Generating final assessment...</p>
          ) : null}

          {finalAssessmentState.status === "error" ? (
            <p role="alert">{finalAssessmentState.message}</p>
          ) : null}

          {finalAssessmentState.status === "success" ? (
            <FinalAssessmentPanel
              assessment={finalAssessmentState.assessment}
            />
          ) : null}
        </>
      ) : null}
    </main>
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