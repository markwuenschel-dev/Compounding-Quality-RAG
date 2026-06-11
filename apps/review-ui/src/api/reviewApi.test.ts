import { afterEach, describe, expect, it, vi } from "vitest";
import {
  createChecklist,
  createFinalAssessment,
  retrieveEvidence,
  ReviewApiError,
} from "./reviewApi";
import type {
  ApiErrorResponse,
  ChecklistResponse,
  FinalAssessmentResponse,
  RetrieveResponse,
} from "./types";

describe("reviewApi", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("posts concern text to the checklist endpoint and returns the checklist response", async () => {
    const responseBody: ChecklistResponse = {
      concernType: "flavor_related_vomiting",
      riskLane: "unexpected_non_life_threatening",
      reviewScope: "full_quality_review",
      initialTakeaway: "Review vomiting timing and rule out severe triggers.",
      requiredChecks: [
        {
          key: "record_review",
          label: "Record review",
          required: true,
          reason: "Confirm relevant compounding and dispensing fields.",
        },
      ],
      missingInformation: ["Dose administered"],
      escalationTriggersToRuleOut: ["pet_hospitalization"],
      evidence: [
        {
          sourceId: "SOP-004",
          sourceTitle: "Customer Context and Administration Review",
          sectionHeading: "Vomiting After Administration",
        },
      ],
      limitations: ["Does not access real customer history."],
    };

    const fetchMock = mockJsonResponse(200, responseBody);

    const result = await createChecklist({
      concernText: "Dog vomited once after flavored oral liquid.",
    });

    expect(result).toEqual(responseBody);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith("/api/checklist", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        concernText: "Dog vomited once after flavored oral liquid.",
      }),
    });
  });

  it("posts retrieval query and preserves evidence fields needed by evidence cards", async () => {
    const responseBody: RetrieveResponse = {
      queryText: "vomiting after administration",
      topK: 5,
      evidence: [
        {
          chunkId: "SOP-004#vomiting-after-administration",
          sourceId: "SOP-004",
          sourceTitle: "Customer Context and Administration Review",
          sourceType: "sop",
          sectionHeading: "Vomiting After Administration",
          score: 0.91,
          matchedTerms: ["vomiting", "administration"],
          supportingText: "Vomiting after administration requires clinical context review.",
        },
      ],
    };

    const fetchMock = mockJsonResponse(200, responseBody);

    const result = await retrieveEvidence({
      queryText: "vomiting after administration",
      topK: 5,
    });

    expect(result.evidence[0]?.chunkId).toBe(
      "SOP-004#vomiting-after-administration",
    );
    expect(result.evidence[0]?.matchedTerms).toEqual([
      "vomiting",
      "administration",
    ]);
    expect(fetchMock).toHaveBeenCalledWith("/api/retrieve", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        queryText: "vomiting after administration",
        topK: 5,
      }),
    });
  });

  it("posts review summary findings to the final assessment endpoint", async () => {
    const responseBody: FinalAssessmentResponse = {
      rawIntake: {
        intakeSource: "qre_general_question_form",
        submitterRole: "customer",
        submissionPurpose: "customer_reported_concern",
        concernNarrative: "Dog vomited once after flavored oral liquid.",
        starRating: null,
        reviewTextPresent: null,
        submitterSelectedClassification: null,
      },
      productContext: {
        species: "dog",
        dosageForm: "oral_liquid",
        productPlaceholder: null,
        flavorOrAttribute: "chicken",
        budPresent: null,
        batchLotPresent: null,
      },
      investigationRequirements: {
        recordReviewRequired: true,
        lotBatchReviewRequired: true,
        inventoryInspectionRequired: true,
        trendScanRequired: true,
        customerOutreachRequired: true,
        frontlineGuidanceLookupRequired: false,
        technicalServicesResponseRequired: true,
      },
      reviewSummary: {
        recordReviewResult: "no_discrepancy_found",
        lotBatchPatternSummary: "no_similar_batch_concerns_found",
        inventoryInspectionResult: "no_inventory_available",
        customerContextSummary: "Vomited once and recovered.",
        apiReferenceReviewResult: "not_needed",
        missingInformation: ["Exact dose administered"],
        evidenceLimitations: ["Inventory was unavailable."],
        severeTriggersObserved: [],
      },
      derivedAssessment: {
        reviewerAssignedClassification: "qre",
        reviewerAssignedCategory: "suspected_ade",
        reviewerAssignedSubcategory: "flavor_related_ade",
        concernType: "flavor_related_vomiting",
        riskLane: "unexpected_non_life_threatening",
        reviewScope: "full_quality_review",
        escalationTriggers: [],
        handlingPath: "technical_services_customer_outreach",
        resolutionReviewRequired: true,
        resolutionOptions: ["counseling_or_follow_up"],
        rationale: "Vomiting after administration supports suspected ADE review.",
      },
    };

    const fetchMock = mockJsonResponse(200, responseBody);

    const result = await createFinalAssessment({
      concernText: "Dog vomited once after flavored oral liquid.",
      topK: 5,
      reviewSummary: {
        recordReviewResult: "no_discrepancy_found",
        lotBatchPatternSummary: "no_similar_batch_concerns_found",
        inventoryInspectionResult: "no_inventory_available",
        customerContextSummary: "Vomited once and recovered.",
        apiReferenceReviewResult: "not_needed",
        missingInformation: ["Exact dose administered"],
        evidenceLimitations: ["Inventory was unavailable."],
        severeTriggersObserved: [],
      },
    });

    expect(result.derivedAssessment?.handlingPath).toBe(
      "technical_services_customer_outreach",
    );
    expect(fetchMock).toHaveBeenCalledWith("/api/final-assessment", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        concernText: "Dog vomited once after flavored oral liquid.",
        topK: 5,
        reviewSummary: {
          recordReviewResult: "no_discrepancy_found",
          lotBatchPatternSummary: "no_similar_batch_concerns_found",
          inventoryInspectionResult: "no_inventory_available",
          customerContextSummary: "Vomited once and recovered.",
          apiReferenceReviewResult: "not_needed",
          missingInformation: ["Exact dose administered"],
          evidenceLimitations: ["Inventory was unavailable."],
          severeTriggersObserved: [],
        },
      }),
    });
  });

  it("throws ReviewApiError with backend validation details when Spring returns ApiErrorResponse", async () => {
    const errorBody: ApiErrorResponse = {
      timestamp: "2026-06-11T17:30:00Z",
      status: 400,
      error: "Bad Request",
      message: "Validation failed",
      path: "/api/checklist",
      requestId: "req-123",
      fieldErrors: [
        {
          field: "concernText",
          message: "concernText must not be blank",
          rejectedValue: "",
          code: "NotBlank",
        },
      ],
      code: "VALIDATION_ERROR",
    };

    mockJsonResponse(400, errorBody);

    await expect(createChecklist({ concernText: "" })).rejects.toMatchObject({
      name: "ReviewApiError",
      status: 400,
      message: "Validation failed",
      details: errorBody,
    });
  });

  it("throws ReviewApiError with a fallback message when the backend error body is not the standard API error shape", async () => {
    mockJsonResponse(502, {
      unexpected: "proxy failure",
    });

    await expect(
      retrieveEvidence({ queryText: "vomiting", topK: 5 }),
    ).rejects.toMatchObject({
      name: "ReviewApiError",
      status: 502,
      message: "Request failed with status 502",
      details: null,
    });
  });

  it("throws ReviewApiError when the server returns invalid JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("not-json", { status: 200 })),
    );

    await expect(
      createChecklist({ concernText: "Dog vomited once." }),
    ).rejects.toMatchObject({
      name: "ReviewApiError",
      status: 200,
      message: "Response was not valid JSON.",
      details: null,
    });
  });

  it("surfaces network failures without converting them into ReviewApiError", async () => {
    const networkError = new TypeError("Failed to fetch");

    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw networkError;
      }),
    );

    await expect(
      createChecklist({ concernText: "Dog vomited once." }),
    ).rejects.toBe(networkError);
  });
});

function mockJsonResponse(status: number, body: unknown) {
  const fetchMock = vi.fn(async () => {
    return new Response(JSON.stringify(body), {
      status,
      headers: {
        "Content-Type": "application/json",
      },
    });
  });

  vi.stubGlobal("fetch", fetchMock);

  return fetchMock;
}