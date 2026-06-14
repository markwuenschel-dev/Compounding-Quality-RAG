import { describe, expect, it } from "vitest";
import type { FinalAssessmentResponse } from "../api/types";
import { formatAssessmentSummary } from "./assessmentSummary";

describe("formatAssessmentSummary", () => {
  it("formats the derived assessment into readable plain text", () => {
    const summary = formatAssessmentSummary(buildAssessment());

    expect(summary).toContain("Compounding Quality Final Assessment");
    expect(summary).toContain("Classification: qre");
    expect(summary).toContain(
      "Handling path: technical_services_customer_outreach",
    );
    expect(summary).toContain("Resolution review required: Yes");
    expect(summary).toContain("- counseling_or_follow_up");
    expect(summary).toContain("Rationale:\nFollow up with the customer.");
  });

  it("handles a missing derived assessment", () => {
    const assessment = buildAssessment();
    assessment.derivedAssessment = null;

    expect(formatAssessmentSummary(assessment)).toContain(
      "No derived assessment was returned.",
    );
  });
});

function buildAssessment(): FinalAssessmentResponse {
  return {
    rawIntake: null,
    productContext: null,
    investigationRequirements: null,
    reviewSummary: null,
    derivedAssessment: {
      reviewerAssignedClassification: "qre",
      reviewerAssignedCategory: "suspected_ade",
      reviewerAssignedSubcategory: "flavor_related_ade",
      concernType: "flavor_related_vomiting",
      riskLane: "unexpected_non_life_threatening",
      reviewScope: "full_quality_review",
      escalationTriggers: [],
      handlingPath: "technical_services_customer_outreach",
      resolutionReviewRequired: true,
      resolutionOptions: ["counseling_or_follow_up"],
      rationale: "Follow up with the customer.",
    },
  };
}
