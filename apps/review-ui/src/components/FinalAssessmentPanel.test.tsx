import { render, screen, waitFor, within } from "@testing-library/react";
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

describe("FinalAssessmentPanel pipeline detail", () => {
  it("surfaces raw intake, product context, requirements, and review summary", async () => {
    const user = userEvent.setup();
    render(<FinalAssessmentPanel assessment={buildFullAssessment()} />);

    await user.click(
      screen.getByRole("button", { name: /Full pipeline output/ }),
    );

    const intake = screen.getByLabelText("Raw intake");
    expect(within(intake).getByText("Customer review")).toBeInTheDocument();

    const product = screen.getByLabelText("Product context");
    expect(within(product).getByText("Dog")).toBeInTheDocument();

    const requirements = screen.getByLabelText("Investigation requirements");
    expect(
      within(requirements).getByText("Record review"),
    ).toBeInTheDocument();

    const summary = screen.getByLabelText("Confirmed review summary");
    expect(
      within(summary).getByText("No discrepancy found"),
    ).toBeInTheDocument();
    expect(
      within(summary).getByText("Possible contamination"),
    ).toBeInTheDocument();
  });

  it("omits the pipeline detail group when no upstream fields are present", () => {
    render(<FinalAssessmentPanel assessment={buildAssessment()} />);

    expect(
      screen.queryByText("Full pipeline output"),
    ).not.toBeInTheDocument();
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

function buildFullAssessment(): FinalAssessmentResponse {
  return {
    ...buildAssessment(),
    rawIntake: {
      intakeSource: "customer_review",
      submitterRole: "pet_owner",
      submissionPurpose: "report_concern",
      concernNarrative: "Dog vomited once after the dose.",
      starRating: 2,
      reviewTextPresent: true,
      submitterSelectedClassification: "adverse_event",
    },
    productContext: {
      species: "dog",
      dosageForm: "oral_liquid",
      productPlaceholder: "Compounded suspension",
      flavorOrAttribute: "chicken",
      budPresent: true,
      batchLotPresent: false,
    },
    investigationRequirements: {
      recordReviewRequired: true,
      lotBatchReviewRequired: false,
      inventoryInspectionRequired: false,
      trendScanRequired: true,
      customerOutreachRequired: true,
      frontlineGuidanceLookupRequired: false,
      technicalServicesResponseRequired: true,
    },
    reviewSummary: {
      recordReviewResult: "no_discrepancy_found",
      lotBatchPatternSummary: "no_similar_batch_concerns_found",
      inventoryInspectionResult: "no_inventory_available",
      customerContextSummary: "Owner reports the dog recovered.",
      apiReferenceReviewResult: "not_needed",
      missingInformation: ["Exact dose administered"],
      evidenceLimitations: ["Inventory was not available to inspect."],
      severeTriggersObserved: ["possible_contamination"],
    },
  };
}