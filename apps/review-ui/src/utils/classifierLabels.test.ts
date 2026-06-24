import { describe, expect, it } from "vitest";
import {
  formatClassifier,
  formatClassifierList,
} from "./classifierLabels";

describe("formatClassifier", () => {
  it("maps known enum values to curated human labels", () => {
    expect(formatClassifier("leadership_escalation_before_resolution")).toBe(
      "Leadership escalation before resolution",
    );
    expect(formatClassifier("suspected_ADE")).toBe(
      "Suspected adverse drug event",
    );
    expect(formatClassifier("QRE")).toBe("Quality-related event (QRE)");
    expect(formatClassifier("sop")).toBe("SOP");
  });

  it("also maps the legacy leADErship typo to the correct label", () => {
    expect(formatClassifier("leADErship_escalation_before_resolution")).toBe(
      "Leadership escalation before resolution",
    );
  });

  it("falls back to sentence case for unmapped values", () => {
    expect(formatClassifier("some_unmapped_value")).toBe("Some unmapped value");
  });

  it("returns null for null or blank input", () => {
    expect(formatClassifier(null)).toBeNull();
    expect(formatClassifier("   ")).toBeNull();
  });
});

describe("formatClassifierList", () => {
  it("maps each value and preserves order", () => {
    expect(
      formatClassifierList(["pet_death", "possible_contamination"]),
    ).toEqual(["Pet death", "Possible contamination"]);
  });
});
