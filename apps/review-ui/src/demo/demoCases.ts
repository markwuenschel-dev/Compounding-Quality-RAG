import type { ReviewSummaryRequest } from "../api/types";

export type DemoCaseId = "vomiting-concern" | "unsupported-record-access";

export type DemoCase = {
  id: DemoCaseId;
  label: string;
  description: string;
  concernText: string;
  reviewSummary?: ReviewSummaryRequest;
};

export const DEFAULT_DEMO_CASE_ID: DemoCaseId = "vomiting-concern";

export const DEMO_CASES: readonly DemoCase[] = [
  {
    id: "vomiting-concern",
    label: "Vomiting concern",
    description:
      "Runs the complete checklist and final-assessment workflow using the primary synthetic demonstration case.",
    concernText:
      "My dog received a chicken-flavored compounded oral liquid. About 10 minutes later he started running around frantically and vomited once. He seems okay now, but I’m worried the medication or flavor caused it.",
    reviewSummary: {
      recordReviewResult: "no_discrepancy_found",
      lotBatchPatternSummary: "no_similar_batch_concerns_found",
      inventoryInspectionResult: "no_inventory_available",
      customerContextSummary:
        "Dog vomited once about 10 minutes after administration and recovered. No hospitalization, death, legal threat, contamination concern, wrong medication concern, or veterinarian allegation was reported.",
      apiReferenceReviewResult: "not_needed",
      missingInformation: ["Exact dose administered"],
      evidenceLimitations: ["Inventory was not available to inspect"],
      severeTriggersObserved: [],
    },
  },
  {
    id: "unsupported-record-access",
    label: "Unsupported record access",
    description:
      "Demonstrates the public boundary by asking the application to inspect real operational records.",
    concernText:
      "Can you look at the real compounding record and tell me whether this batch had the same vomiting complaints?",
  },
] as const;

export function getDemoCase(id: DemoCaseId): DemoCase {
  const demoCase = DEMO_CASES.find((candidate) => candidate.id === id);

  if (!demoCase) {
    throw new Error(`Unknown demo case: ${id}`);
  }

  return demoCase;
}
