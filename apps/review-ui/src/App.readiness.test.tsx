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
import { useBackendReadiness } from "./hooks/useBackendReadiness";

vi.mock("./hooks/useBackendReadiness", () => ({
  useBackendReadiness: vi.fn(),
}));

vi.mock("./api/reviewApi", async () => {
  const actual =
    await vi.importActual<typeof import("./api/reviewApi")>(
      "./api/reviewApi",
    );

  return {
    ...actual,
    createChecklist: vi.fn(),
    createFinalAssessment: vi.fn(),
  };
});

const useBackendReadinessMock =
  vi.mocked(useBackendReadiness);
const createChecklistMock = vi.mocked(createChecklist);
const createFinalAssessmentMock =
  vi.mocked(createFinalAssessment);

describe("App readiness and retry behavior", () => {
  beforeEach(() => {
    createChecklistMock.mockReset();
    createFinalAssessmentMock.mockReset();
    useBackendReadinessMock.mockReturnValue(
      readyBackend(),
    );
  });

  it("disables checklist submission while the backend is unavailable", async () => {
    const user = userEvent.setup();

    useBackendReadinessMock.mockReturnValue({
      ...readyBackend(),
      status: "unavailable",
      message: "Backend unavailable: Python unavailable.",
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
    expect(
      screen.getByText(
        "Backend unavailable: Python unavailable.",
      ),
    ).toBeInTheDocument();
  });

  it("retries a retryable checklist failure", async () => {
    const user = userEvent.setup();

    createChecklistMock
      .mockRejectedValueOnce(
        new ReviewApiError(
          "Failed to fetch.",
          "network",
          0,
          null,
          true,
        ),
      )
      .mockResolvedValueOnce(buildChecklist());

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
      await screen.findByText(
        "Cannot reach the review API. Confirm the backend is running and try again.",
      ),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", {
        name: "Retry checklist",
      }),
    );

    expect(createChecklistMock).toHaveBeenCalledTimes(2);
    expect(
      await screen.findByRole("heading", {
        name: "Checklist result",
      }),
    ).toBeInTheDocument();
  });

  it("does not offer retry for validation failures", async () => {
    const user = userEvent.setup();

    createChecklistMock.mockRejectedValueOnce(
      new ReviewApiError(
        "concernText must not be blank",
        "validation",
        400,
        {
          timestamp: "2026-06-14T12:00:00Z",
          status: 400,
          error: "Bad Request",
          message: "concernText must not be blank",
          path: "/api/checklist",
          requestId: "request-1",
          fieldErrors: [],
          code: "VALIDATION_ERROR",
        },
        false,
      ),
    );

    render(<App />);

    await user.type(
      screen.getByLabelText("Concern text"),
      "x",
    );
    await user.click(
      screen.getByRole("button", {
        name: "Generate checklist",
      }),
    );

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent("concernText must not be blank");
    expect(
      screen.queryByRole("button", {
        name: "Retry checklist",
      }),
    ).not.toBeInTheDocument();
  });

  it("retries a retryable final assessment failure", async () => {
    const user = userEvent.setup();

    createChecklistMock.mockResolvedValue(buildChecklist());
    createFinalAssessmentMock
      .mockRejectedValueOnce(
        new ReviewApiError(
          "Engine unavailable.",
          "engine",
          502,
          null,
          true,
        ),
      )
      .mockResolvedValueOnce(buildFinalAssessment());

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

    await screen.findByRole("heading", {
      name: "Reviewer findings",
    });

    const form = screen.getByRole("form", {
      name: "Final assessment form",
    });

    changeField(form, /record review result/i, "none");
    changeField(form, /lot or batch pattern summary/i, "none");
    changeField(
      form,
      /inventory inspection result/i,
      "unavailable",
    );
    changeField(
      form,
      /api reference review result/i,
      "not_needed",
    );

    await user.click(
      within(form).getByRole("button", {
        name: "Generate final assessment",
      }),
    );

    expect(
      await screen.findByText(
        "The review engine could not complete the request. Check backend readiness and try again.",
      ),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", {
        name: "Retry final assessment",
      }),
    );

    await waitFor(() => {
      expect(createFinalAssessmentMock)
        .toHaveBeenCalledTimes(2);
    });

    expect(
      await screen.findByRole("heading", {
        name: "Final assessment result",
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

function changeField(
  form: HTMLElement,
  name: RegExp,
  value: string,
) {
  fireEvent.change(
    within(form).getByRole("textbox", { name }),
    {
      target: { value },
    },
  );
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

function buildFinalAssessment(): FinalAssessmentResponse {
  return {
    rawIntake: null,
    productContext: null,
    investigationRequirements: null,
    reviewSummary: null,
    derivedAssessment: {
      reviewerAssignedClassification: "qre",
      reviewerAssignedCategory: "suspected_ade",
      reviewerAssignedSubcategory: "vomiting",
      concernType: "flavor_related_vomiting",
      riskLane: "unexpected_non_life_threatening",
      reviewScope: "full_quality_review",
      escalationTriggers: [],
      handlingPath: "technical_services_customer_outreach",
      resolutionReviewRequired: true,
      resolutionOptions: ["customer_follow_up"],
      rationale: "Follow up with the customer.",
    },
  };
}
