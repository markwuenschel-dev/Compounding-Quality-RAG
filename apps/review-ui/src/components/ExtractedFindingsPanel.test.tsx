import {
  render,
  screen,
} from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ExtractedFindingsPanel } from "./ExtractedFindingsPanel";

describe("ExtractedFindingsPanel", () => {
  it("renders supporting quotes and unresolved questions", () => {
    render(
      <ExtractedFindingsPanel
        extraction={{
          reviewSummary: {
            recordReviewResult:
              "no_discrepancy_found",
            lotBatchPatternSummary: "unavailable",
            inventoryInspectionResult:
              "not_checked",
            customerContextSummary: null,
            apiReferenceReviewResult:
              "not_needed",
            missingInformation: [],
            evidenceLimitations: [],
            severeTriggersObserved: [],
          },
          fieldEvidence: [
            {
              fieldName: "record_review_result",
              status: "normalized",
              supportingQuote:
                "Worksheet review found no discrepancy.",
              explanation:
                "Normalized into the enum contract.",
            },
          ],
          unresolvedQuestions: [
            {
              fieldName: "dose_administered",
              question:
                "What dose was administered?",
              reason: "Dose context is missing.",
              decisionImpact: ["review_scope"],
            },
          ],
        }}
      />,
    );

    expect(
      screen.getByText(
        "Worksheet review found no discrepancy.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "What dose was administered?",
      ),
    ).toBeInTheDocument();
  });
});
