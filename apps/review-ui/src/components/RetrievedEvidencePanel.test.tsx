import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { RetrieveResponse } from "../api/types";
import { RetrievedEvidencePanel } from "./RetrievedEvidencePanel";

describe("RetrievedEvidencePanel", () => {
  it("renders ranked chunks with score, matched terms, and supporting text", () => {
    render(<RetrievedEvidencePanel retrieval={buildRetrieval()} />);

    expect(screen.getByText("Top 3")).toBeInTheDocument();
    expect(
      screen.getByText("Flavor-related vomiting guidance"),
    ).toBeInTheDocument();
    expect(screen.getByText("0.870")).toBeInTheDocument();
    expect(screen.getByText("vomiting")).toBeInTheDocument();
    expect(screen.getByText("flavor")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Mild transient vomiting after a flavored oral liquid is commonly self-limiting.",
      ),
    ).toBeInTheDocument();
  });

  it("renders an empty state when no chunks are retrieved", () => {
    render(
      <RetrievedEvidencePanel
        retrieval={{ queryText: "vomiting", topK: 3, evidence: [] }}
      />,
    );

    expect(
      screen.getByText("No evidence chunks were retrieved."),
    ).toBeInTheDocument();
  });
});

function buildRetrieval(): RetrieveResponse {
  return {
    queryText: "Dog vomited once after a flavored compound.",
    topK: 3,
    evidence: [
      {
        chunkId: "chunk-1",
        sourceId: "SRC-001",
        sourceTitle: "Flavor-related vomiting guidance",
        sourceType: "synthetic_guidance",
        sectionHeading: "Transient GI signs",
        score: 0.87,
        matchedTerms: ["vomiting", "flavor"],
        supportingText:
          "Mild transient vomiting after a flavored oral liquid is commonly self-limiting.",
      },
    ],
  };
}
