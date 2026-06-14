import { afterEach, describe, expect, it, vi } from "vitest";
import {
  createChecklist,
  createFinalAssessment,
  getReadiness,
  retrieveEvidence,
  ReviewApiError,
} from "./reviewApi";
import type {
  ApiErrorResponse,
  ChecklistResponse,
  FinalAssessmentResponse,
  ReadinessResponse,
  RetrieveResponse,
} from "./types";

describe("reviewApi", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("posts checklist requests and returns JSON responses", async () => {
    const responseBody = buildChecklistResponse();
    const fetchMock = mockJsonResponse(200, responseBody);

    const result = await createChecklist({
      concernText: "Dog vomited once.",
    });

    expect(result).toEqual(responseBody);
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

    const fetchMock = mockJsonResponse(200, responseBody);

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

  it("posts final assessment requests", async () => {
    const responseBody: FinalAssessmentResponse = {
      rawIntake: null,
      productContext: null,
      investigationRequirements: null,
      reviewSummary: null,
      derivedAssessment: null,
    };

    const fetchMock = mockJsonResponse(200, responseBody);

    await createFinalAssessment({
      concernText: "Dog vomited once.",
      reviewSummary: {
        recordReviewResult: "none",
        lotBatchPatternSummary: "none",
        inventoryInspectionResult: "unavailable",
        apiReferenceReviewResult: "not_needed",
        missingInformation: [],
        evidenceLimitations: [],
        severeTriggersObserved: [],
      },
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/final-assessment",
      expect.objectContaining({
        method: "POST",
      }),
    );
  });

  it("returns readiness bodies even when the endpoint responds 503", async () => {
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

    await expect(getReadiness()).resolves.toEqual(readiness);
  });

  it("classifies browser network failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      }),
    );

    await expect(
      createChecklist({ concernText: "Dog vomited once." }),
    ).rejects.toMatchObject({
      name: "ReviewApiError",
      kind: "network",
      retryable: true,
    });
  });

  it("aborts and classifies timed-out requests", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_input: RequestInfo | URL, init?: RequestInit) =>
          new Promise<Response>((_resolve, reject) => {
            init?.signal?.addEventListener("abort", () => {
              reject(new DOMException("Aborted", "AbortError"));
            });
          }),
      ),
    );

    await expect(
      createChecklist(
        { concernText: "Dog vomited once." },
        { timeoutMs: 1 },
      ),
    ).rejects.toMatchObject({
      name: "ReviewApiError",
      kind: "timeout",
      retryable: true,
    });
  });

  it("classifies validation failures as non-retryable", async () => {
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
      status: 400,
    });
  });

  it("classifies engine failures as retryable", async () => {
    mockJsonResponse(
      502,
      buildApiError(
        502,
        "ENGINE_PROCESS_START",
        "Python process failed to start",
      ),
    );

    await expect(
      createChecklist({ concernText: "Dog vomited once." }),
    ).rejects.toMatchObject({
      kind: "engine",
      retryable: true,
      status: 502,
    });
  });

  it("classifies unsupported-access refusals as non-retryable", async () => {
    mockJsonResponse(
      403,
      buildApiError(
        403,
        "UNSUPPORTED_ACCESS",
        "Real operational records are not available.",
      ),
    );

    await expect(
      createChecklist({
        concernText: "Check the real compounding record.",
      }),
    ).rejects.toMatchObject({
      kind: "refusal",
      retryable: false,
      status: 403,
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
      createChecklist({ concernText: "Dog vomited once." }),
    ).rejects.toMatchObject({
      kind: "invalid_response",
      retryable: true,
    });
  });
});

function mockJsonResponse(status: number, body: unknown) {
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
