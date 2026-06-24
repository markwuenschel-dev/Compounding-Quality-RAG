import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { CollapsibleCard } from "./CollapsibleCard";

describe("CollapsibleCard", () => {
  it("hides the body and shows the summary when collapsed", () => {
    render(
      <CollapsibleCard
        ariaLabel="Card"
        title="My step"
        summary="3 items"
        collapsed
        onToggleCollapsed={() => {}}
      >
        <p>Body content</p>
      </CollapsibleCard>,
    );

    expect(
      screen.getByRole("heading", { name: "My step" }),
    ).toBeInTheDocument();
    expect(screen.getByText("3 items")).toBeInTheDocument();
    expect(screen.queryByText("Body content")).not.toBeInTheDocument();
  });

  it("shows the body and fires the toggle when the header is clicked", async () => {
    const user = userEvent.setup();
    const onToggle = vi.fn();

    render(
      <CollapsibleCard
        ariaLabel="Card"
        title="My step"
        collapsed={false}
        onToggleCollapsed={onToggle}
      >
        <p>Body content</p>
      </CollapsibleCard>,
    );

    expect(screen.getByText("Body content")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { expanded: true }));

    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it("is a static, always-open card when no toggle handler is given", () => {
    render(
      <CollapsibleCard ariaLabel="Card" title="My step">
        <p>Body content</p>
      </CollapsibleCard>,
    );

    expect(screen.getByText("Body content")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
