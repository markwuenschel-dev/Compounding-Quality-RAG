import type {
  ApiErrorResponse,
  ChecklistRequest,
  ChecklistResponse,
  FinalAssessmentRequest,
  FinalAssessmentResponse,
  ReadinessResponse,
  RetrieveRequest,
  RetrieveResponse,
} from "./types";

const DEFAULT_API_BASE_URL = "";
const DEFAULT_REQUEST_TIMEOUT_MS = 15_000;
const READINESS_TIMEOUT_MS = 5_000;

export type ReviewApiErrorKind =
  | "network"
  | "timeout"
  | "validation"
  | "engine"
  | "refusal"
  | "http"
  | "invalid_response";

export type RequestOptions = {
  timeoutMs?: number;
};

export class ReviewApiError extends Error {
  readonly kind: ReviewApiErrorKind;
  readonly status: number;
  readonly details: ApiErrorResponse | null;
  readonly retryable: boolean;

  constructor(
    message: string,
    kind: ReviewApiErrorKind,
    status: number,
    details: ApiErrorResponse | null,
    retryable: boolean,
  ) {
    super(message);
    this.name = "ReviewApiError";
    this.kind = kind;
    this.status = status;
    this.details = details;
    this.retryable = retryable;
  }
}

export async function getReadiness(
  options?: RequestOptions,
): Promise<ReadinessResponse> {
  const { body } = await requestJson(
    "/ready",
    {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    },
    options?.timeoutMs ?? READINESS_TIMEOUT_MS,
  );

  if (!isReadinessResponse(body)) {
    throw invalidResponseError(0);
  }

  return body;
}

export async function createChecklist(
  request: ChecklistRequest,
  options?: RequestOptions,
): Promise<ChecklistResponse> {
  return postJson<ChecklistRequest, ChecklistResponse>(
    "/api/checklist",
    request,
    options,
  );
}

export async function retrieveEvidence(
  request: RetrieveRequest,
  options?: RequestOptions,
): Promise<RetrieveResponse> {
  return postJson<RetrieveRequest, RetrieveResponse>(
    "/api/retrieve",
    request,
    options,
  );
}

export async function createFinalAssessment(
  request: FinalAssessmentRequest,
  options?: RequestOptions,
): Promise<FinalAssessmentResponse> {
  return postJson<FinalAssessmentRequest, FinalAssessmentResponse>(
    "/api/final-assessment",
    request,
    options,
  );
}

export function getReviewApiErrorMessage(
  error: unknown,
  fallbackMessage: string,
): string {
  if (!(error instanceof ReviewApiError)) {
    return fallbackMessage;
  }

  switch (error.kind) {
    case "network":
      return "Cannot reach the review API. Confirm the backend is running and try again.";
    case "timeout":
      return "The request timed out before the review engine responded. Try again.";
    case "validation":
      return error.details?.message ?? "The request contains invalid or incomplete data.";
    case "engine":
      return "The review engine could not complete the request. Check backend readiness and try again.";
    case "refusal":
      return (
        error.details?.message ??
        "This request is outside the supported synthetic-data boundary."
      );
    case "invalid_response":
      return "The backend returned a response the UI could not understand.";
    default:
      return error.message || fallbackMessage;
  }
}

async function postJson<TRequest, TResponse>(
  path: string,
  request: TRequest,
  options?: RequestOptions,
): Promise<TResponse> {
  const { response, body } = await requestJson(
    path,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(request),
    },
    options?.timeoutMs ?? DEFAULT_REQUEST_TIMEOUT_MS,
  );

  if (!response.ok) {
    throw createHttpError(response.status, body);
  }

  if (body === null || typeof body !== "object") {
    throw invalidResponseError(response.status);
  }

  return body as TResponse;
}

async function requestJson(
  path: string,
  init: RequestInit,
  timeoutMs: number,
): Promise<{ response: Response; body: unknown }> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${DEFAULT_API_BASE_URL}${path}`, {
      ...init,
      signal: controller.signal,
    });
    const body = await readJsonResponse(response);

    return { response, body };
  } catch (error) {
    if (isAbortError(error)) {
      throw new ReviewApiError(
        "Request timed out.",
        "timeout",
        0,
        null,
        true,
      );
    }

    if (error instanceof TypeError) {
      throw new ReviewApiError(
        "Failed to fetch.",
        "network",
        0,
        null,
        true,
      );
    }

    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

async function readJsonResponse(response: Response): Promise<unknown> {
  const text = await response.text();

  if (text.length === 0) {
    return null;
  }

  try {
    return JSON.parse(text) as unknown;
  } catch {
    throw invalidResponseError(response.status);
  }
}

function createHttpError(status: number, body: unknown): ReviewApiError {
  const details = isApiErrorResponse(body) ? body : null;
  const code = details?.code?.toUpperCase() ?? "";
  const message =
    details?.message ?? `Request failed with status ${status}`;

  if (
    status === 403 ||
    code.includes("REFUSAL") ||
    code.includes("UNSUPPORTED_ACCESS")
  ) {
    return new ReviewApiError(
      message,
      "refusal",
      status,
      details,
      false,
    );
  }

  if (
    status === 408 ||
    status === 504 ||
    code.includes("TIMEOUT")
  ) {
    return new ReviewApiError(
      message,
      "timeout",
      status,
      details,
      true,
    );
  }

  if (
    status === 400 ||
    status === 422 ||
    code.includes("VALIDATION")
  ) {
    return new ReviewApiError(
      message,
      "validation",
      status,
      details,
      false,
    );
  }

  if (
    status >= 500 ||
    code.includes("ENGINE") ||
    code.includes("RAG")
  ) {
    return new ReviewApiError(
      message,
      "engine",
      status,
      details,
      true,
    );
  }

  return new ReviewApiError(
    message,
    "http",
    status,
    details,
    status >= 500,
  );
}

function invalidResponseError(status: number): ReviewApiError {
  return new ReviewApiError(
    "Response was not valid JSON.",
    "invalid_response",
    status,
    null,
    true,
  );
}

function isAbortError(error: unknown): boolean {
  return (
    error instanceof DOMException &&
    error.name === "AbortError"
  );
}

function isApiErrorResponse(value: unknown): value is ApiErrorResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const candidate = value as Partial<ApiErrorResponse>;

  return (
    typeof candidate.status === "number" &&
    typeof candidate.message === "string"
  );
}

function isReadinessResponse(value: unknown): value is ReadinessResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const candidate = value as Partial<ReadinessResponse>;

  return (
    (candidate.status === "READY" ||
      candidate.status === "NOT_READY") &&
    Array.isArray(candidate.checks) &&
    typeof candidate.timestamp === "string"
  );
}
