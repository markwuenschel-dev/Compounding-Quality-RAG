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
import { ReviewSummaryForm } from "./ReviewSummaryForm";

describe("ReviewSummaryForm", () => {
  it("submits canonical enum values", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn(async () => {});

    render(
      <ReviewSummaryForm
        isSubmitting={false}
        onSubmit={onSubmit}
        initialValues={{
          recordReviewResult:
            "no_discrepancy_found",
          lotBatchPatternSummary:
            "no_similar_batch_concerns_found",
          inventoryInspectionResult:
            "no_inventory_available",
          customerContextSummary:
            "Dog recovered.",
          apiReferenceReviewResult:
            "not_needed",
          missingInformation: [],
          evidenceLimitations: [],
          severeTriggersObserved: [],
        }}
      />,
    );

    await user.click(
      screen.getByRole("button", {
        name: "Generate final assessment",
      }),
    );

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        recordReviewResult:
          "no_discrepancy_found",
        lotBatchPatternSummary:
          "no_similar_batch_concerns_found",
        inventoryInspectionResult:
          "no_inventory_available",
        apiReferenceReviewResult:
          "not_needed",
      }),
    );
  });
});
