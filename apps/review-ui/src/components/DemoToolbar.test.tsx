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
        topK={3}
        onTopKChange={vi.fn()}
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

  it("reports the chosen retrieval depth", async () => {
    const user = userEvent.setup();
    const onTopKChange = vi.fn();

    render(
      <DemoToolbar
        selectedDemoCaseId="vomiting-concern"
        onSelectedDemoCaseChange={vi.fn()}
        onLoadDemoCase={vi.fn()}
        onStartOver={vi.fn()}
        canStartOver
        topK={3}
        onTopKChange={onTopKChange}
      />,
    );

    await user.selectOptions(
      screen.getByLabelText("Chunks to retrieve"),
      "5",
    );

    expect(onTopKChange).toHaveBeenCalledWith(5);
  });

  it("disables Start over when there is no workflow state", () => {
    render(
      <DemoToolbar
        selectedDemoCaseId="vomiting-concern"
        onSelectedDemoCaseChange={vi.fn()}
        onLoadDemoCase={vi.fn()}
        onStartOver={vi.fn()}
        canStartOver={false}
        topK={3}
        onTopKChange={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Start over" }),
    ).toBeDisabled();
  });
});
