import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { ReviewApiError } from "./api/reviewApi";
import type { ChecklistResponse } from "./api/types";

vi.mock("./api/reviewApi", async () => {
  const actual =
    await vi.importActual<typeof import("./api/reviewApi")>("./api/reviewApi");

  return {
    ...actual,
    createChecklist: vi.fn(),
  };
});

import { createChecklist } from "./api/reviewApi";

const createChecklistMock = vi.mocked(createChecklist);

describe("App", () => {
  beforeEach(() => {
    createChecklistMock.mockReset();
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
    const checklist = buildChecklistResponse();

    createChecklistMock.mockResolvedValueOnce(checklist);

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

  it("renders backend validation errors from the API client", async () => {
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

  it("renders generic network errors", async () => {
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

  it("trims concern text before submitting", async () => {
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
});

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