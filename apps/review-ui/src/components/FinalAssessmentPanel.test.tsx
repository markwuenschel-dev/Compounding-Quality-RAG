import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { FinalAssessmentResponse } from "../api/types";
import { FinalAssessmentPanel } from "./FinalAssessmentPanel";

describe("FinalAssessmentPanel copy action", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("copies a readable assessment summary", async () => {
    const user = userEvent.setup();
    const writeText = vi
      .spyOn(navigator.clipboard, "writeText")
      .mockResolvedValue(undefined);

    render(<FinalAssessmentPanel assessment={buildAssessment()} />);

    await user.click(
      screen.getByRole("button", { name: "Copy assessment summary" }),
    );

    await waitFor(() => {
      expect(writeText).toHaveBeenCalledWith(
        expect.stringContaining(
          "Handling path: technical_services_customer_outreach",
        ),
      );
    });

    expect(
      await screen.findByText("Copied assessment summary."),
    ).toBeInTheDocument();
  });

  it("shows an error when clipboard writing fails", async () => {
    const user = userEvent.setup();

    vi.spyOn(navigator.clipboard, "writeText").mockRejectedValueOnce(
      new Error("clipboard blocked"),
    );

    render(<FinalAssessmentPanel assessment={buildAssessment()} />);

    await user.click(
      screen.getByRole("button", { name: "Copy assessment summary" }),
    );

    expect(
      await screen.findByText("Unable to copy assessment summary."),
    ).toBeInTheDocument();
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