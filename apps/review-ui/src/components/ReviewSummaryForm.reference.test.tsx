import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { ReviewSummaryForm } from "./ReviewSummaryForm";


describe("ReviewSummaryForm reference-review options", () => {
  it("includes completed external reference review", () => {
    render(
      <ReviewSummaryForm
        isSubmitting={false}
        onSubmit={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("option", {
        name: "External reference consulted",
      }),
    ).toBeInTheDocument();
  });
});
