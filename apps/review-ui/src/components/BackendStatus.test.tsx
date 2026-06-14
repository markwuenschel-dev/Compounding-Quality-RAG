import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { BackendStatus } from "./BackendStatus";
import type { BackendReadinessState } from "../hooks/useBackendReadiness";

describe("BackendStatus", () => {
  it("renders the ready state", () => {
    render(
      <BackendStatus
        readiness={buildReadiness({
          status: "ready",
          message: "Backend ready",
        })}
      />,
    );

    expect(screen.getByText("Backend ready")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Check again" }),
    ).not.toBeInTheDocument();
  });

  it("renders unavailable details and refreshes on request", async () => {
    const user = userEvent.setup();
    const refresh = vi.fn(async () => {});

    render(
      <BackendStatus
        readiness={buildReadiness({
          status: "unavailable",
          message: "Backend unavailable: Python unavailable.",
          refresh,
        })}
      />,
    );

    expect(
      screen.getByText(
        "Backend unavailable: Python unavailable.",
      ),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: "Check again" }),
    );

    expect(refresh).toHaveBeenCalledTimes(1);
  });
});

function buildReadiness(
  overrides: Partial<BackendReadinessState>,
): BackendReadinessState {
  return {
    status: "checking",
    response: null,
    message: "Checking backend readiness...",
    isRefreshing: false,
    refresh: async () => {},
    ...overrides,
  };
}
