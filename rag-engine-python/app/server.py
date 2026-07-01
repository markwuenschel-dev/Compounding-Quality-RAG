from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from pydantic import Field

from app.checklist import build_intake_checklist
from app.checklist_models import IntakeChecklist
from app.llm_client import LLMClientError, openai_json_client_from_env
from app.review_pipeline import (
    ReviewRefused,
    run_checklist as run_checklist_pipeline,
    run_final_assessment as run_final_assessment_pipeline,
    run_retrieve as run_retrieve_pipeline,
)
from app.retrieval import DEFAULT_CHUNKS_PATH as CANONICAL_CHUNKS_PATH
from app.retrieval import SearchResult, retrieve
from app.review_summary_extraction import extract_review_summary_result
from app.schemas import (
    ExpectedStructuredOutput,
    ReviewSummary,
    ReviewSummaryExtractionResult,
    SourceType,
    StrictBaseModel,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    logger.addHandler(stderr_handler)

DEFAULT_CHUNKS_PATH = Path(
    os.getenv("RAG_CHUNKS_PATH", str(CANONICAL_CHUNKS_PATH))
)
DEFAULT_TOP_K = int(os.getenv("RAG_TOP_K", "5"))

app = FastAPI(
    title="Compounding Quality RAG Engine",
    version="0.1.0",
)


@app.middleware("http")
async def log_request_correlation(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id", "")

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_id=%s method=%s path=%s status_code=error",
            request_id,
            request.method,
            request.url.path,
        )
        raise

    response.headers["X-Request-Id"] = request_id
    logger.info(
        "request_id=%s method=%s path=%s status_code=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
    )

    return response


class HealthResponse(StrictBaseModel):
    status: str


class ReadinessResponse(StrictBaseModel):
    status: str
    checks: dict[str, str]


class ChecklistRequest(StrictBaseModel):
    concern_text: str = Field(min_length=1)
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=20)


class RetrieveRequest(StrictBaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=20)
    source_type: str | None = SourceType.SOP.value


class RetrieveResponse(StrictBaseModel):
    query: str
    results: list[SearchResult]


class FinalAssessmentRequest(StrictBaseModel):
    concern_text: str = Field(min_length=1)
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=20)
    review_summary: ReviewSummary


class ReviewSummaryExtractorRequest(StrictBaseModel):
    reviewer_note: str = Field(min_length=1)
    concern_text: str = ""


@app.get("/health", response_model=HealthResponse)
@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/readiness", response_model=ReadinessResponse)
@app.get("/api/readiness", response_model=ReadinessResponse)
def readiness() -> ReadinessResponse:
    checks = {
        "chunks_path": "ok" if DEFAULT_CHUNKS_PATH.exists() else "missing",
        "engine": "ok",
    }
    status = "ready" if all(value == "ok" for value in checks.values()) else "not_ready"

    return ReadinessResponse(status=status, checks=checks)


@app.post("/checklist", response_model=IntakeChecklist)
@app.post("/api/checklist", response_model=IntakeChecklist)
def checklist(request: ChecklistRequest) -> IntakeChecklist:
    try:
        return run_checklist_pipeline(
            request.concern_text,
            top_k=request.top_k,
            build_intake_checklist=lambda concern_text, *, top_k: build_intake_checklist(
                concern_text,
                chunks_path=DEFAULT_CHUNKS_PATH,
                top_k=top_k,
            ),
        )
    except ReviewRefused as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Checklist generation failed")
        raise HTTPException(status_code=500, detail="Checklist generation failed") from exc


@app.post("/retrieve", response_model=RetrieveResponse)
@app.post("/api/retrieve", response_model=RetrieveResponse)
def retrieve_evidence(request: RetrieveRequest) -> RetrieveResponse:
    try:
        results = run_retrieve_pipeline(
            request.query,
            top_k=request.top_k,
            source_type=request.source_type,
            retrieve=lambda *, query, top_k, source_type: retrieve(
                query=query,
                chunks_path=DEFAULT_CHUNKS_PATH,
                top_k=top_k,
                source_type=source_type,
            ),
        )

        return RetrieveResponse(query=request.query, results=results)
    except ReviewRefused as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Retrieval failed")
        raise HTTPException(status_code=500, detail="Retrieval failed") from exc


@app.post("/final-assessment", response_model=ExpectedStructuredOutput)
@app.post("/api/final-assessment", response_model=ExpectedStructuredOutput)
def final_assessment(request: FinalAssessmentRequest) -> ExpectedStructuredOutput:
    try:
        return run_final_assessment_pipeline(
            request.concern_text,
            request.review_summary,
            top_k=request.top_k,
            build_intake_checklist=lambda concern_text, *, top_k: build_intake_checklist(
                concern_text,
                chunks_path=DEFAULT_CHUNKS_PATH,
                top_k=top_k,
            ),
        )
    except ReviewRefused as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Final assessment failed")
        raise HTTPException(status_code=500, detail="Final assessment failed") from exc


@app.post("/review-summary/extract", response_model=ReviewSummaryExtractionResult)
@app.post("/api/review-summary/extract", response_model=ReviewSummaryExtractionResult)
def extract_review_summary(
    request: ReviewSummaryExtractorRequest,
) -> ReviewSummaryExtractionResult:
    try:
        llm_client = openai_json_client_from_env()

        return extract_review_summary_result(
            reviewer_note=request.reviewer_note,
            llm_client=llm_client,
            concern_text=request.concern_text,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LLMClientError as exc:
        logger.exception("LLM client failed")
        raise HTTPException(status_code=502, detail="LLM client failed") from exc
    except Exception as exc:
        logger.exception("Review summary extraction failed")
        raise HTTPException(status_code=500, detail="Review summary extraction failed") from exc