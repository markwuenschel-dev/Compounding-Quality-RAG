type WorkflowProgressProps = {
  checklistStatus: "idle" | "loading" | "success" | "error";
  finalAssessmentStatus: "idle" | "loading" | "success" | "error";
};

type StepState = "upcoming" | "current" | "complete";

export function WorkflowProgress({
  checklistStatus,
  finalAssessmentStatus,
}: WorkflowProgressProps) {
  const currentStep = getCurrentStep(checklistStatus, finalAssessmentStatus);

  const steps = [
    { number: 1, label: "Concern" },
    { number: 2, label: "Checklist" },
    { number: 3, label: "Reviewer findings" },
    { number: 4, label: "Final assessment" },
  ];

  return (
    <nav className="workflow-progress" aria-label="Review progress">
      <ol>
        {steps.map((step) => {
          const state = getStepState(step.number, currentStep);

          return (
            <li
              key={step.number}
              className={`workflow-step workflow-step-${state}`}
              aria-current={state === "current" ? "step" : undefined}
            >
              <span className="step-number">{step.number}</span>
              <span className="step-label">{step.label}</span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

function getCurrentStep(
  checklistStatus: WorkflowProgressProps["checklistStatus"],
  finalAssessmentStatus: WorkflowProgressProps["finalAssessmentStatus"],
): number {
  if (
    finalAssessmentStatus === "loading" ||
    finalAssessmentStatus === "success"
  ) {
    return 4;
  }

  if (checklistStatus === "success") {
    return 3;
  }

  if (checklistStatus === "loading") {
    return 2;
  }

  return 1;
}

function getStepState(stepNumber: number, currentStep: number): StepState {
  if (stepNumber < currentStep) {
    return "complete";
  }

  if (stepNumber === currentStep) {
    return "current";
  }

  return "upcoming";
}
