import {
  render,
  screen,
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
  extractReviewSummary,
  ReviewApiError,
} from "./api/reviewApi";
import type {
  ChecklistResponse,
  ReviewSummaryExtractResponse,
} from "./api/types";
import { useBackendReadiness } from "./hooks/useBackendReadiness";

vi.mock("./hooks/useBackendReadiness", () => ({
  useBackendReadiness: vi.fn(),
}));

vi.mock("./api/reviewApi", async () => {
  const actual =
    await vi.importActual<
      typeof import("./api/reviewApi")
    >("./api/reviewApi");

  return {
    ...actual,
    createChecklist: vi.fn(),
    extractReviewSummary: vi.fn(),
    createFinalAssessment: vi.fn(),
  };
});

const readinessMock =
  vi.mocked(useBackendReadiness);
const createChecklistMock =
  vi.mocked(createChecklist);
const extractionMock =
  vi.mocked(extractReviewSummary);

describe("App readiness and extraction retry", () => {
  beforeEach(() => {
    createChecklistMock.mockReset();
    extractionMock.mockReset();
    readinessMock.mockReturnValue(readyBackend());
  });

  it("disables checklist submission while unavailable", async () => {
    const user = userEvent.setup();

    readinessMock.mockReturnValue({
      ...readyBackend(),
      status: "unavailable",
      message:
        "Backend unavailable: Python unavailable.",
    });

    render(<App />);

    await user.type(
      screen.getByLabelText("Concern text"),
      "Dog vomited once.",
    );

    expect(
      screen.getByRole("button", {
        name: "Generate checklist",
      }),
    ).toBeDisabled();
  });

  it("retries a transient extraction failure", async () => {
    const user = userEvent.setup();

    createChecklistMock.mockResolvedValue(
      buildChecklist(),
    );
    extractionMock
      .mockRejectedValueOnce(
        new ReviewApiError(
          "OpenAI request failed.",
          "engine",
          502,
          null,
          true,
        ),
      )
      .mockResolvedValueOnce(buildExtraction());

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
      "Worksheet reviewed.",
    );
    await user.click(
      screen.getByRole("button", {
        name: "Extract reviewer findings",
      }),
    );

    expect(
      await screen.findByRole("button", {
        name: "Retry extraction",
      }),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", {
        name: "Retry extraction",
      }),
    );

    expect(extractionMock).toHaveBeenCalledTimes(2);
    expect(
      await screen.findByRole("heading", {
        name: "Extracted findings",
      }),
    ).toBeInTheDocument();
  });
});

function readyBackend() {
  return {
    status: "ready" as const,
    response: {
      status: "READY" as const,
      checks: [],
      timestamp: "2026-06-14T12:00:00Z",
    },
    message: "Backend ready",
    isRefreshing: false,
    refresh: async () => {},
  };
}

function buildChecklist(): ChecklistResponse {
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

function buildExtraction(): ReviewSummaryExtractResponse {
  return {
    reviewSummary: {
      recordReviewResult:
        "no_discrepancy_found",
      lotBatchPatternSummary: "unavailable",
      inventoryInspectionResult: "not_checked",
      customerContextSummary: null,
      apiReferenceReviewResult: "not_needed",
      missingInformation: [],
      evidenceLimitations: [],
      severeTriggersObserved: [],
    },
    fieldEvidence: [],
    unresolvedQuestions: [],
  };
}
