import type {
  ApiErrorResponse,
  ChecklistRequest,
  ChecklistResponse,
  FinalAssessmentRequest,
  FinalAssessmentResponse,
  RetrieveRequest,
  RetrieveResponse,
} from "./types";

const DEFAULT_API_BASE_URL = "";

export class ReviewApiError extends Error {
  readonly status: number;
  readonly details: ApiErrorResponse | null;

  constructor(message: string, status: number, details: ApiErrorResponse | null) {
    super(message);
    this.name = "ReviewApiError";
    this.status = status;
    this.details = details;
  }
}

export async function createChecklist(
  request: ChecklistRequest,
): Promise<ChecklistResponse> {
  return postJson<ChecklistRequest, ChecklistResponse>("/api/checklist", request);
}

export async function retrieveEvidence(
  request: RetrieveRequest,
): Promise<RetrieveResponse> {
  return postJson<RetrieveRequest, RetrieveResponse>("/api/retrieve", request);
}

export async function createFinalAssessment(
  request: FinalAssessmentRequest,
): Promise<FinalAssessmentResponse> {
  return postJson<FinalAssessmentRequest, FinalAssessmentResponse>(
    "/api/final-assessment",
    request,
  );
}

async function postJson<TRequest, TResponse>(
  path: string,
  request: TRequest,
): Promise<TResponse> {
  const response = await fetch(`${DEFAULT_API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(request),
  });

  const responseBody = await readJsonResponse(response);

  if (!response.ok) {
    const errorDetails = isApiErrorResponse(responseBody) ? responseBody : null;
    const message =
      errorDetails?.message ??
      `Request failed with status ${response.status}`;

    throw new ReviewApiError(message, response.status, errorDetails);
  }

  return responseBody as TResponse;
}

async function readJsonResponse(response: Response): Promise<unknown> {
  const text = await response.text();

  if (text.length === 0) {
    return null;
  }

  try {
    return JSON.parse(text) as unknown;
  } catch {
    throw new ReviewApiError(
      "Response was not valid JSON.",
      response.status,
      null,
    );
  }
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