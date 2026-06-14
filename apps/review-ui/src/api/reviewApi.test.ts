import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import {
  createChecklist,
  createFinalAssessment,
  extractReviewSummary,
  getReadiness,
  retrieveEvidence,
} from "./reviewApi";
import type {
  ApiErrorResponse,
  ChecklistResponse,
  FinalAssessmentResponse,
  ReadinessResponse,
  RetrieveResponse,
  ReviewSummaryExtractResponse,
} from "./types";

describe("reviewApi", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("posts checklist requests", async () => {
    const responseBody = buildChecklistResponse();
    const fetchMock = mockJsonResponse(
      200,
      responseBody,
    );

    await createChecklist({
      concernText: "Dog vomited once.",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/checklist",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          concernText: "Dog vomited once.",
        }),
      }),
    );
  });

  it("posts retrieval requests", async () => {
    const responseBody: RetrieveResponse = {
      queryText: "vomiting",
      topK: 5,
      evidence: [],
    };
    const fetchMock = mockJsonResponse(
      200,
      responseBody,
    );

    await retrieveEvidence({
      queryText: "vomiting",
      topK: 5,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/retrieve",
      expect.objectContaining({
        method: "POST",
      }),
    );
  });

  it("posts review-summary extraction requests", async () => {
    const responseBody =
      buildExtractionResponse();
    const fetchMock = mockJsonResponse(
      200,
      responseBody,
    );

    const result = await extractReviewSummary({
      concernText: "Dog vomited.",
      pharmacistNotes:
        "Worksheet review found no discrepancy.",
    });

    expect(result).toEqual(responseBody);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/review-summary/extract",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          concernText: "Dog vomited.",
          pharmacistNotes:
            "Worksheet review found no discrepancy.",
        }),
      }),
    );
  });

  it("posts final assessment requests", async () => {
    const responseBody: FinalAssessmentResponse = {
      rawIntake: null,
      productContext: null,
      investigationRequirements: null,
      reviewSummary: null,
      derivedAssessment: null,
    };
    const fetchMock = mockJsonResponse(
      200,
      responseBody,
    );

    await createFinalAssessment({
      concernText: "Dog vomited once.",
      reviewSummary:
        buildExtractionResponse().reviewSummary,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/final-assessment",
      expect.objectContaining({
        method: "POST",
      }),
    );
  });

  it("returns readiness bodies for 503", async () => {
    const readiness: ReadinessResponse = {
      status: "NOT_READY",
      checks: [
        {
          name: "pythonCommand",
          status: "DOWN",
          detail: "Python unavailable.",
        },
      ],
      timestamp: "2026-06-14T12:00:00Z",
    };

    mockJsonResponse(503, readiness);

    await expect(getReadiness()).resolves.toEqual(
      readiness,
    );
  });

  it("classifies browser network failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      }),
    );

    await expect(
      createChecklist({
        concernText: "Dog vomited once.",
      }),
    ).rejects.toMatchObject({
      kind: "network",
      retryable: true,
    });
  });

  it("classifies timed-out requests", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (
          _input: RequestInfo | URL,
          init?: RequestInit,
        ) =>
          new Promise<Response>(
            (_resolve, reject) => {
              init?.signal?.addEventListener(
                "abort",
                () => {
                  reject(
                    new DOMException(
                      "Aborted",
                      "AbortError",
                    ),
                  );
                },
              );
            },
          ),
      ),
    );

    await expect(
      createChecklist(
        { concernText: "Dog vomited once." },
        { timeoutMs: 1 },
      ),
    ).rejects.toMatchObject({
      kind: "timeout",
      retryable: true,
    });
  });

  it("classifies validation failures", async () => {
    mockJsonResponse(
      400,
      buildApiError(
        400,
        "VALIDATION_ERROR",
        "concernText must not be blank",
      ),
    );

    await expect(
      createChecklist({ concernText: "" }),
    ).rejects.toMatchObject({
      kind: "validation",
      retryable: false,
    });
  });

  it("classifies extraction failures as engine failures", async () => {
    mockJsonResponse(
      502,
      buildApiError(
        502,
        "EXTRACTION_FAILURE",
        "OpenAI request failed.",
      ),
    );

    await expect(
      extractReviewSummary({
        concernText: "Dog vomited.",
        pharmacistNotes: "Reviewed.",
      }),
    ).rejects.toMatchObject({
      kind: "engine",
      retryable: true,
    });
  });

  it("classifies REFUSED responses as refusal errors", async () => {
    mockJsonResponse(
      422,
      buildApiError(
        422,
        "REFUSED",
        "Real operational records are unavailable.",
      ),
    );

    await expect(
      createChecklist({
        concernText:
          "Check the real compounding record.",
      }),
    ).rejects.toMatchObject({
      kind: "refusal",
      retryable: false,
    });
  });

  it("classifies invalid JSON responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response("not-json", {
            status: 200,
          }),
      ),
    );

    await expect(
      createChecklist({
        concernText: "Dog vomited once.",
      }),
    ).rejects.toMatchObject({
      kind: "invalid_response",
      retryable: true,
    });
  });
});

function mockJsonResponse(
  status: number,
  body: unknown,
) {
  const fetchMock = vi.fn(
    async () =>
      new Response(JSON.stringify(body), {
        status,
        headers: {
          "Content-Type": "application/json",
        },
      }),
  );

  vi.stubGlobal("fetch", fetchMock);

  return fetchMock;
}

function buildApiError(
  status: number,
  code: string,
  message: string,
): ApiErrorResponse {
  return {
    timestamp: "2026-06-14T12:00:00Z",
    status,
    error: "Request failed",
    message,
    path: "/api/checklist",
    requestId: "request-1",
    fieldErrors: [],
    code,
  };
}

function buildChecklistResponse(): ChecklistResponse {
  return {
    concernType: "flavor_related_vomiting",
    riskLane: "unexpected_non_life_threatening",
    reviewScope: "full_quality_review",
    initialTakeaway: "Review the concern.",
    requiredChecks: [],
    missingInformation: [],
    escalationTriggersToRuleOut: [],
    evidence: [],
    limitations: [],
  };
}

function buildExtractionResponse(): ReviewSummaryExtractResponse {
  return {
    reviewSummary: {
      recordReviewResult:
        "no_discrepancy_found",
      lotBatchPatternSummary: "unavailable",
      inventoryInspectionResult: "not_checked",
      customerContextSummary: "Dog vomited once.",
      apiReferenceReviewResult: "not_needed",
      missingInformation: [
        "Exact dose administered",
      ],
      evidenceLimitations: [],
      severeTriggersObserved: [],
    },
    fieldEvidence: [],
    unresolvedQuestions: [],
  };
}
