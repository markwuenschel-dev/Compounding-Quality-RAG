import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DemoToolbar } from "./DemoToolbar";

describe("DemoToolbar", () => {
  it("changes the selected case and invokes operator actions", async () => {
    const user = userEvent.setup();
    const onSelectedDemoCaseChange = vi.fn();
    const onLoadDemoCase = vi.fn();
    const onStartOver = vi.fn();

    render(
      <DemoToolbar
        selectedDemoCaseId="vomiting-concern"
        onSelectedDemoCaseChange={onSelectedDemoCaseChange}
        onLoadDemoCase={onLoadDemoCase}
        onStartOver={onStartOver}
        canStartOver
      />,
    );

    await user.selectOptions(
      screen.getByLabelText("Demo case"),
      "unsupported-record-access",
    );
    await user.click(screen.getByRole("button", { name: "Load demo case" }));
    await user.click(screen.getByRole("button", { name: "Start over" }));

    expect(onSelectedDemoCaseChange).toHaveBeenCalledWith(
      "unsupported-record-access",
    );
    expect(onLoadDemoCase).toHaveBeenCalledTimes(1);
    expect(onStartOver).toHaveBeenCalledTimes(1);
  });

  it("disables Start over when there is no workflow state", () => {
    render(
      <DemoToolbar
        selectedDemoCaseId="vomiting-concern"
        onSelectedDemoCaseChange={vi.fn()}
        onLoadDemoCase={vi.fn()}
        onStartOver={vi.fn()}
        canStartOver={false}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Start over" }),
    ).toBeDisabled();
  });
});
