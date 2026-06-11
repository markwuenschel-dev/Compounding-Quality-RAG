import { useState } from "react";
import { createChecklist, ReviewApiError } from "./api/reviewApi";
import type { ChecklistResponse } from "./api/types";
import { ChecklistPanel } from "./components/ChecklistPanel";
import { ConcernInputForm } from "./components/ConcernInputForm";

type ChecklistState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; checklist: ChecklistResponse }
  | { status: "error"; message: string };

export function App() {
  const [checklistState, setChecklistState] = useState<ChecklistState>({
    status: "idle",
  });

  async function handleChecklistSubmit(concernText: string) {
    setChecklistState({ status: "loading" });

    try {
      const checklist = await createChecklist({ concernText });
      setChecklistState({ status: "success", checklist });
    } catch (error) {
      setChecklistState({
        status: "error",
        message: getChecklistErrorMessage(error),
      });
    }
  }

  return (
    <main>
      <h1>Compounding Quality Review</h1>
      <p>
        Enter a synthetic concern narrative to generate a review-support
        checklist.
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
        <ChecklistPanel checklist={checklistState.checklist} />
      ) : null}
    </main>
  );
}

function getChecklistErrorMessage(error: unknown): string {
  if (error instanceof ReviewApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to generate checklist.";
}