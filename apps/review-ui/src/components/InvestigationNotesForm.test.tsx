import {
  render,
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";
import { InvestigationNotesForm } from "./InvestigationNotesForm";

describe("InvestigationNotesForm", () => {
  it("submits one trimmed narrative", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn(async () => {});

    render(
      <InvestigationNotesForm
        isSubmitting={false}
        onSubmit={onSubmit}
      />,
    );

    await user.type(
      screen.getByLabelText(
        "Investigation and actions taken",
      ),
      "  worksheet checked; nothing off  ",
    );
    await user.click(
      screen.getByRole("button", {
        name: "Extract reviewer findings",
      }),
    );

    expect(onSubmit).toHaveBeenCalledWith(
      "worksheet checked; nothing off",
    );
  });

  it("disables extraction for blank notes", () => {
    render(
      <InvestigationNotesForm
        isSubmitting={false}
        onSubmit={async () => {}}
      />,
    );

    expect(
      screen.getByRole("button", {
        name: "Extract reviewer findings",
      }),
    ).toBeDisabled();
  });
});
