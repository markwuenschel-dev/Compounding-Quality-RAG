import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import {
  createChecklist,
  createFinalAssessment,
  ReviewApiError,
} from "./api/reviewApi";
import type {
  ChecklistResponse,
  FinalAssessmentResponse,
} from "./api/types";
import { FinalAssessmentPanel } from "./components/FinalAssessmentPanel";

vi.mock("./api/reviewApi", async () => {
  const actual =
    await vi.importActual<typeof import("./api/reviewApi")>("./api/reviewApi");

  return {
    ...actual,
    createChecklist: vi.fn(),
    createFinalAssessment: vi.fn(),
  };
});

const createChecklistMock = vi.mocked(createChecklist);
const createFinalAssessmentMock = vi.mocked(createFinalAssessment);

describe("App", () => {
  beforeEach(() => {
    createChecklistMock.mockReset();
    createFinalAssessmentMock.mockReset();
  });

  it("renders the initial checklist workflow screen", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { name: "Compounding Quality Review" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Concern text")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Generate checklist" }),
    ).toBeDisabled();
    expect(screen.getByText("No checklist generated yet.")).toBeInTheDocument();
  });

  it("submits concern text and renders the checklist response", async () => {
    const user = userEvent.setup();

    createChecklistMock.mockResolvedValueOnce(buildChecklistResponse());

    render(<App />);

    await user.type(
      screen.getByLabelText("Concern text"),
      "Dog vomited once after receiving chicken-flavored oral liquid.",
    );

    await user.click(
      screen.getByRole("button", { name: "Generate checklist" }),
    );

    expect(createChecklistMock).toHaveBeenCalledWith({
      concernText:
        "Dog vomited once after receiving chicken-flavored oral liquid.",
    });

    expect(
      await screen.findByRole("heading", { name: "Checklist result" }),
    ).toBeInTheDocument();

    expect(screen.getByText("flavor_related_vomiting")).toBeInTheDocument();
    expect(
      screen.getByText("unexpected_non_life_threatening"),
    ).toBeInTheDocument();
    expect(screen.getByText("Record review")).toBeInTheDocument();
    expect(screen.getByText("Dose administered")).toBeInTheDocument();
    expect(screen.getByText("SOP-004")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Reviewer findings" }),
    ).toBeInTheDocument();
  });

  it("shows loading state while checklist request is pending", async () => {
    const user = userEvent.setup();

    createChecklistMock.mockImplementationOnce(
      () => new Promise<ChecklistResponse>(() => {}),
    );

    render(<App />);

    await user.type(screen.getByLabelText("Concern text"), "Dog vomited once.");
    await user.click(
      screen.getByRole("button", { name: "Generate checklist" }),
    );

    expect(screen.getByRole("status")).toHaveTextContent(
      "Generating checklist...",
    );
    expect(
      screen.getByRole("button", { name: "Generating checklist..." }),
    ).toBeDisabled();
  });

  it("renders backend validation errors from the checklist API client", async () => {
    const user = userEvent.setup();

    createChecklistMock.mockRejectedValueOnce(
      new ReviewApiError("concernText must not be blank", 400, {
        timestamp: "2026-06-11T20:00:00Z",
        status: 400,
        error: "Bad Request",
        message: "concernText must not be blank",
        path: "/api/checklist",
        requestId: "req-1",
        fieldErrors: [],
        code: "VALIDATION_ERROR",
      }),
    );

    render(<App />);

    await user.type(screen.getByLabelText("Concern text"), "x");
    await user.click(
      screen.getByRole("button", { name: "Generate checklist" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "concernText must not be blank",
    );
  });

  it("renders generic checklist network errors", async () => {
    const user = userEvent.setup();

    createChecklistMock.mockRejectedValueOnce(new TypeError("Failed to fetch"));

    render(<App />);

    await user.type(screen.getByLabelText("Concern text"), "Dog vomited once.");
    await user.click(
      screen.getByRole("button", { name: "Generate checklist" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Failed to fetch",
    );
  });

  it("trims concern text before submitting the checklist request", async () => {
    const user = userEvent.setup();

    createChecklistMock.mockResolvedValueOnce(buildChecklistResponse());

    render(<App />);

    await user.type(
      screen.getByLabelText("Concern text"),
      "   Dog vomited once.   ",
    );

    await user.click(
      screen.getByRole("button", { name: "Generate checklist" }),
    );

    await waitFor(() => {
      expect(createChecklistMock).toHaveBeenCalledWith({
        concernText: "Dog vomited once.",
      });
    });
  });

  it("keeps final assessment submission disabled until required findings are complete", async () => {
    const user = userEvent.setup();

    createChecklistMock.mockResolvedValueOnce(buildChecklistResponse());

    render(<App />);

    await user.type(screen.getByLabelText("Concern text"), "Dog vomited once.");
    await user.click(
      screen.getByRole("button", { name: "Generate checklist" }),
    );

    await screen.findByRole("heading", { name: "Reviewer findings" });

    const submitButton = screen.getByRole("button", {
      name: "Generate final assessment",
    });

    expect(submitButton).toBeDisabled();

    await user.type(
      getFinalAssessmentTextbox(/record review result/i),
      "No compounding deviations found.",
    );
    await user.type(
      getFinalAssessmentTextbox(/lot or batch pattern summary/i),
      "No related trend found.",
    );
    await user.type(
      getFinalAssessmentTextbox(/inventory inspection result/i),
      "No abnormal inventory findings.",
    );

    expect(submitButton).toBeDisabled();

    await user.type(
      getFinalAssessmentTextbox(/api reference review result/i),
      "No active product-specific stability exception found.",
    );

    expect(submitButton).toBeEnabled();
  });

  it("submits reviewer findings and renders the final assessment response", async () => {
    const user = userEvent.setup();

    createChecklistMock.mockResolvedValueOnce(buildChecklistResponse());
    createFinalAssessmentMock.mockResolvedValueOnce(
      buildFinalAssessmentResponse(),
    );

    render(<App />);

    await user.type(
      screen.getByLabelText("Concern text"),
      "Dog vomited once after receiving chicken-flavored oral liquid.",
    );
    await user.click(
      screen.getByRole("button", { name: "Generate checklist" }),
    );

    await screen.findByRole("heading", { name: "Reviewer findings" });

    changeFinalAssessmentTextbox(
      /record review result/i,
      "No compounding deviations found.",
    );
    changeFinalAssessmentTextbox(
      /lot or batch pattern summary/i,
      "No related trend found.",
    );
    changeFinalAssessmentTextbox(
      /inventory inspection result/i,
      "No abnormal inventory findings.",
    );
    changeFinalAssessmentTextbox(
      /customer context summary/i,
      "Customer reported one vomiting event.",
    );
    changeFinalAssessmentTextbox(
      /api reference review result/i,
      "No active product-specific stability exception found.",
    );
    changeFinalAssessmentTextbox(
      /missing information/i,
      "Exact administration time\nMeal timing",
    );
    changeFinalAssessmentTextbox(
      /evidence limitations/i,
      "No direct patient history access",
    );
    changeFinalAssessmentTextbox(
      /severe triggers observed/i,
      "None observed",
    );

    await user.click(
      screen.getByRole("button", { name: "Generate final assessment" }),
    );

    expect(createFinalAssessmentMock).toHaveBeenCalledWith({
      concernText:
        "Dog vomited once after receiving chicken-flavored oral liquid.",
      topK: 3,
      reviewSummary: {
        recordReviewResult: "No compounding deviations found.",
        lotBatchPatternSummary: "No related trend found.",
        inventoryInspectionResult: "No abnormal inventory findings.",
        customerContextSummary: "Customer reported one vomiting event.",
        apiReferenceReviewResult:
          "No active product-specific stability exception found.",
        missingInformation: ["Exact administration time", "Meal timing"],
        evidenceLimitations: ["No direct patient history access"],
        severeTriggersObserved: ["None observed"],
      },
    });

    expect(
      await screen.findByRole("heading", { name: "Final assessment result" }),
    ).toBeInTheDocument();

    expect(screen.getByText("Product Complaint")).toBeInTheDocument();
    expect(screen.getByText("Technical Services Review")).toBeInTheDocument();
    expect(screen.getByText("Customer follow-up")).toBeInTheDocument();
  });

  it("renders final assessment API errors", async () => {
    const user = userEvent.setup();

    createChecklistMock.mockResolvedValueOnce(buildChecklistResponse());
    createFinalAssessmentMock.mockRejectedValueOnce(
      new ReviewApiError("reviewSummary is required", 400, {
        timestamp: "2026-06-11T20:00:00Z",
        status: 400,
        error: "Bad Request",
        message: "reviewSummary is required",
        path: "/api/final-assessment",
        requestId: "req-2",
        fieldErrors: [],
        code: "VALIDATION_ERROR",
      }),
    );

    render(<App />);

    await user.type(screen.getByLabelText("Concern text"), "Dog vomited once.");
    await user.click(
      screen.getByRole("button", { name: "Generate checklist" }),
    );

    await screen.findByRole("heading", { name: "Reviewer findings" });

    await user.type(
      getFinalAssessmentTextbox(/record review result/i),
      "No compounding deviations found.",
    );
    await user.type(
      getFinalAssessmentTextbox(/lot or batch pattern summary/i),
      "No related trend found.",
    );
    await user.type(
      getFinalAssessmentTextbox(/inventory inspection result/i),
      "No abnormal inventory findings.",
    );
    await user.type(
      getFinalAssessmentTextbox(/api reference review result/i),
      "No active product-specific stability exception found.",
    );

    await user.click(
      screen.getByRole("button", { name: "Generate final assessment" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "reviewSummary is required",
    );
  });
});

describe("FinalAssessmentPanel", () => {
  it("renders resolution review required as Yes when required", () => {
    render(<FinalAssessmentPanel assessment={buildFinalAssessmentResponse()} />);

    const panel = screen.getByLabelText("Final assessment result");

    expect(
      within(panel).getByText("Resolution review required"),
    ).toBeInTheDocument();
    expect(within(panel).getByText("Yes")).toBeInTheDocument();
  });
});

function getFinalAssessmentTextbox(name: string | RegExp): HTMLElement {
  return within(getFinalAssessmentForm()).getByRole("textbox", {
    name,
  });
}

function changeFinalAssessmentTextbox(
  name: string | RegExp,
  value: string,
): void {
  fireEvent.change(getFinalAssessmentTextbox(name), {
    target: { value },
  });
}

function getFinalAssessmentForm(): HTMLElement {
  return screen.getByRole("form", {
    name: "Final assessment form",
  });
}

function buildChecklistResponse(): ChecklistResponse {
  return {
    concernType: "flavor_related_vomiting",
    riskLane: "unexpected_non_life_threatening",
    reviewScope: "full_quality_review",
    initialTakeaway: "Review vomiting timing and rule out severe triggers.",
    requiredChecks: [
      {
        key: "record_review",
        label: "Record review",
        required: true,
        reason: "Confirm relevant compounding and dispensing fields.",
      },
    ],
    missingInformation: ["Dose administered"],
    escalationTriggersToRuleOut: ["pet_hospitalization"],
    evidence: [
      {
        sourceId: "SOP-004",
        sourceTitle: "Customer Context and Administration Review",
        sectionHeading: "Vomiting After Administration",
      },
    ],
    limitations: ["Does not access real customer history."],
  };
}

function buildFinalAssessmentResponse(): FinalAssessmentResponse {
  return {
    rawIntake: {
      intakeSource: "customer_review",
      submitterRole: "customer",
      submissionPurpose: "quality_review",
      concernNarrative:
        "Dog vomited once after receiving chicken-flavored oral liquid.",
      starRating: 2,
      reviewTextPresent: true,
      submitterSelectedClassification: null,
    },
    productContext: {
      species: "dog",
      dosageForm: "oral_liquid",
      productPlaceholder: "Product A",
      flavorOrAttribute: "chicken",
      budPresent: true,
      batchLotPresent: true,
    },
    investigationRequirements: {
      recordReviewRequired: true,
      lotBatchReviewRequired: true,
      inventoryInspectionRequired: true,
      trendScanRequired: true,
      customerOutreachRequired: true,
      frontlineGuidanceLookupRequired: false,
      technicalServicesResponseRequired: true,
    },
    reviewSummary: {
      recordReviewResult: "No compounding deviations found.",
      lotBatchPatternSummary: "No related trend found.",
      inventoryInspectionResult: "No abnormal inventory findings.",
      customerContextSummary: "Customer reported one vomiting event.",
      apiReferenceReviewResult:
        "No active product-specific stability exception found.",
      missingInformation: ["Exact administration time", "Meal timing"],
      evidenceLimitations: ["No direct patient history access"],
      severeTriggersObserved: ["None observed"],
    },
    derivedAssessment: {
      reviewerAssignedClassification: "Product Complaint",
      reviewerAssignedCategory: "Adverse Event",
      reviewerAssignedSubcategory: "Vomiting after administration",
      concernType: "flavor_related_vomiting",
      riskLane: "unexpected_non_life_threatening",
      reviewScope: "full_quality_review",
      escalationTriggers: ["continued vomiting", "hospitalization"],
      handlingPath: "Technical Services Review",
      resolutionReviewRequired: true,
      resolutionOptions: ["Customer follow-up", "Document review outcome"],
      rationale:
        "Single vomiting event requires quality review and customer follow-up before closure.",
    },
  };
}