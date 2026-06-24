import {
  render,
  screen,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import { App } from "./App";
import {
  createChecklist,
  createFinalAssessment,
  extractReviewSummary,
  retrieveEvidence,
} from "./api/reviewApi";
import type {
  ChecklistResponse,
  FinalAssessmentResponse,
  RetrieveResponse,
  ReviewSummaryExtractResponse,
} from "./api/types";
import { FinalAssessmentPanel } from "./components/FinalAssessmentPanel";

vi.mock("./api/reviewApi", async (importOriginal) => {
  const actual =
    await importOriginal<
      typeof import("./api/reviewApi")
    >();

  return {
    ...actual,
    createChecklist: vi.fn(),
    retrieveEvidence: vi.fn(),
    extractReviewSummary: vi.fn(),
    createFinalAssessment: vi.fn(),
  };
});

vi.mock("./hooks/useBackendReadiness", () => ({
  useBackendReadiness: () => ({
    status: "ready",
    response: {
      status: "READY",
      checks: [],
      timestamp: "2026-06-14T12:00:00Z",
    },
    message: "Backend ready",
    isRefreshing: false,
    refresh: async () => {},
  }),
}));

const createChecklistMock =
  vi.mocked(createChecklist);
const retrieveEvidenceMock =
  vi.mocked(retrieveEvidence);
const extractReviewSummaryMock =
  vi.mocked(extractReviewSummary);
const createFinalAssessmentMock =
  vi.mocked(createFinalAssessment);

describe("App", () => {
  beforeEach(() => {
    createChecklistMock.mockReset();
    retrieveEvidenceMock.mockReset();
    extractReviewSummaryMock.mockReset();
    createFinalAssessmentMock.mockReset();
    retrieveEvidenceMock.mockResolvedValue(
      buildRetrieveResponse(),
    );
  });

  it("renders the initial checklist workflow", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", {
        name: "Compounding Quality Review",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Concern text"),
    ).toBeInTheDocument();
  });

  it("shows one pharmacist-notes box after checklist generation", async () => {
    const user = userEvent.setup();
    createChecklistMock.mockResolvedValue(
      buildChecklistResponse(),
    );

    render(<App />);

    await user.type(
      screen.getByLabelText("Concern text"),
      "Dog vomited once.",
    );
    await user.click(
      screen.getByRole("button", {
        name: "Generate checklist",
      }),
    );

    expect(
      await screen.findByRole("heading", {
        name: "Pharmacist investigation notes",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText(
        "Investigation and actions taken",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("form", {
        name: "Final assessment form",
      }),
    ).not.toBeInTheDocument();
  });

  it("extracts notes and prefills canonical confirmation controls", async () => {
    const user = userEvent.setup();
    createChecklistMock.mockResolvedValue(
      buildChecklistResponse(),
    );
    extractReviewSummaryMock.mockResolvedValue(
      buildExtractionResponse(),
    );

    render(<App />);

    await user.type(
      screen.getByLabelText("Concern text"),
      "Dog vomited once.",
    );
    await user.click(
      screen.getByRole("button", {
        name: "Generate checklist",
      }),
    );
    await user.type(
      screen.getByLabelText(
        "Investigation and actions taken",
      ),
      "Worksheet checked; nothing off.",
    );
    await user.click(
      screen.getByRole("button", {
        name: "Extract reviewer findings",
      }),
    );

    expect(
      extractReviewSummaryMock,
    ).toHaveBeenCalledWith({
      concernText: "Dog vomited once.",
      pharmacistNotes:
        "Worksheet checked; nothing off.",
    });

    expect(
      await screen.findByRole("heading", {
        name: "Extracted findings",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByLabelText(
        /record review result/i,
      ),
    ).toHaveValue("no_discrepancy_found");
    expect(
      screen.getByText(
        "What dose was administered?",
      ),
    ).toBeInTheDocument();
  });

  it("submits confirmed structured values to final assessment", async () => {
    const user = userEvent.setup();
    createChecklistMock.mockResolvedValue(
      buildChecklistResponse(),
    );
    extractReviewSummaryMock.mockResolvedValue(
      buildExtractionResponse(),
    );
    createFinalAssessmentMock.mockResolvedValue(
      buildFinalAssessmentResponse(),
    );

    render(<App />);

    await user.type(
      screen.getByLabelText("Concern text"),
      "Dog vomited once.",
    );
    await user.click(
      screen.getByRole("button", {
        name: "Generate checklist",
      }),
    );
    await user.type(
      screen.getByLabelText(
        "Investigation and actions taken",
      ),
      "Worksheet checked; nothing off.",
    );
    await user.click(
      screen.getByRole("button", {
        name: "Extract reviewer findings",
      }),
    );

    await screen.findByRole("form", {
      name: "Final assessment form",
    });

    await user.click(
      screen.getByRole("button", {
        name: "Generate final assessment",
      }),
    );

    expect(
      createFinalAssessmentMock,
    ).toHaveBeenCalledWith({
      concernText: "Dog vomited once.",
      topK: 3,
      reviewSummary:
        buildExtractionResponse().reviewSummary,
    });

    expect(
      await screen.findByRole("heading", {
        name: "Final assessment result",
      }),
    ).toBeInTheDocument();
  });
});

describe("FinalAssessmentPanel", () => {
  it("renders resolution review required as Yes", () => {
    render(
      <FinalAssessmentPanel
        assessment={buildFinalAssessmentResponse()}
      />,
    );

    const panel = screen.getByLabelText(
      "Final assessment result",
    );

    expect(
      within(panel).getByText(
        "Resolution review required",
      ),
    ).toBeInTheDocument();
    expect(
      within(panel).getByText("Yes"),
    ).toBeInTheDocument();
  });
});

function buildChecklistResponse(): ChecklistResponse {
  return {
    concernType: "flavor_related_vomiting",
    riskLane: "unexpected_non_life_threatening",
    reviewScope: "full_quality_review",
    initialTakeaway: "Review the concern.",
    requiredChecks: [],
    missingInformation: [],
    escalationTriggersToRuleOut: [],
    evidence: [],
    limitations: [],
  };
}

function buildRetrieveResponse(): RetrieveResponse {
  return {
    queryText: "Dog vomited once.",
    topK: 3,
    evidence: [],
  };
}

function buildExtractionResponse(): ReviewSummaryExtractResponse {
  return {
    reviewSummary: {
      recordReviewResult:
        "no_discrepancy_found",
      lotBatchPatternSummary:
        "no_similar_batch_concerns_found",
      inventoryInspectionResult:
        "no_inventory_available",
      customerContextSummary:
        "Dog vomited once and recovered.",
      apiReferenceReviewResult: "not_needed",
      missingInformation: [
        "Exact dose administered",
      ],
      evidenceLimitations: [
        "Inventory was not available to inspect.",
      ],
      severeTriggersObserved: [],
    },
    fieldEvidence: [
      {
        fieldName: "record_review_result",
        status: "normalized",
        supportingQuote:
          "Worksheet checked; nothing off.",
        explanation:
          "Normalized into the enum contract.",
      },
    ],
    unresolvedQuestions: [
      {
        fieldName: "dose_administered",
        question: "What dose was administered?",
        reason: "Dose context is missing.",
        decisionImpact: ["review_scope"],
      },
    ],
  };
}

function buildFinalAssessmentResponse(): FinalAssessmentResponse {
  return {
    rawIntake: null,
    productContext: null,
    investigationRequirements: null,
    reviewSummary: null,
    derivedAssessment: {
      reviewerAssignedClassification: "QRE",
      reviewerAssignedCategory: "suspected_ADE",
      reviewerAssignedSubcategory:
        "flavor_related_ADE",
      concernType: "flavor_related_vomiting",
      riskLane:
        "unexpected_non_life_threatening",
      reviewScope: "full_quality_review",
      escalationTriggers: [],
      handlingPath:
        "technical_services_customer_outreach",
      resolutionReviewRequired: true,
      resolutionOptions: [
        "counseling_or_follow_up",
      ],
      rationale: "Follow up with the customer.",
    },
  };
}
