import type { FinalAssessmentResponse } from "../api/types";

export function formatAssessmentSummary(
  assessment: FinalAssessmentResponse,
): string {
  const derived = assessment.derivedAssessment;

  if (!derived) {
    return "Compounding Quality Final Assessment\n\nNo derived assessment was returned.";
  }

  const lines = [
    "Compounding Quality Final Assessment",
    "",
    `Classification: ${valueOrFallback(derived.reviewerAssignedClassification)}`,
    `Category: ${valueOrFallback(derived.reviewerAssignedCategory)}`,
    `Subcategory: ${valueOrFallback(derived.reviewerAssignedSubcategory)}`,
    `Concern type: ${valueOrFallback(derived.concernType)}`,
    `Risk lane: ${valueOrFallback(derived.riskLane)}`,
    `Review scope: ${valueOrFallback(derived.reviewScope)}`,
    `Handling path: ${valueOrFallback(derived.handlingPath)}`,
    `Resolution review required: ${
      derived.resolutionReviewRequired ? "Yes" : "No"
    }`,
    "",
    "Escalation triggers:",
    ...formatList(derived.escalationTriggers),
    "",
    "Resolution options:",
    ...formatList(derived.resolutionOptions),
    "",
    "Rationale:",
    valueOrFallback(derived.rationale),
  ];

  return lines.join("\n");
}

function formatList(values: string[]): string[] {
  return values.length > 0 ? values.map((value) => `- ${value}`) : ["- None"];
}

function valueOrFallback(value: string | null): string {
  return value?.trim() || "Not provided";
}
