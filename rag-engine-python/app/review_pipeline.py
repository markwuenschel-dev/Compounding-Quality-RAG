"""The review pipeline: the single seam that owns review orchestration.

Adapters (the stdin bridge in ``api_runner``, the FastAPI app in ``server``, and
the demo ``cli``) must not sequence the review stages themselves. They call into
this module so the refusal boundary, input validation, and stage ordering live in
one place and cannot drift apart. Outcomes are exposed as domain results and
``ReviewRefused`` — never as transport-specific error codes, so each adapter maps
them to its own protocol without a translation table.
"""

from __future__ import annotations

from collections.abc import Callable

from app.checklist import build_intake_checklist as default_build_intake_checklist
from app.checklist_models import IntakeChecklist
from app.final_assessment import build_final_assessment as default_build_final_assessment
from app.refusal import evaluate_refusal as default_evaluate_refusal
from app.retrieval import SearchResult, retrieve as default_retrieve
from app.schemas import (
    ExpectedStructuredOutput,
    RefusalResult,
    ReviewSummary,
    SourceType,
)


class ReviewRefused(Exception):
    """Raised when the refusal boundary blocks a concern before any stage runs.

    Carries the full :class:`RefusalResult` so adapters can render reason and
    matched terms in whatever shape their transport requires.
    """

    def __init__(self, refusal: RefusalResult) -> None:
        self.refusal = refusal
        super().__init__(
            refusal.message or "Request was refused by review boundary rules."
        )


def _screened_text(
    text: str,
    *,
    top_k: int,
    evaluate_refusal: Callable[[str], RefusalResult],
    blank_message: str,
) -> str:
    """Validate input and enforce the refusal boundary, returning cleaned text.

    Raises ``ValueError`` on blank text or non-positive ``top_k``, and
    ``ReviewRefused`` when the text crosses the refusal boundary. This is the one
    place every pipeline entry point screens its input, so the boundary can never
    be applied inconsistently across stages.
    """
    clean_text = text.strip()
    if not clean_text:
        raise ValueError(blank_message)

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    refusal = evaluate_refusal(clean_text)
    if refusal.refused:
        raise ReviewRefused(refusal)

    return clean_text


def run_checklist(
    concern_text: str,
    *,
    top_k: int = 5,
    build_intake_checklist: Callable[..., IntakeChecklist] = default_build_intake_checklist,
    evaluate_refusal: Callable[[str], RefusalResult] = default_evaluate_refusal,
) -> IntakeChecklist:
    """Validate, screen against the refusal boundary, then build the checklist.

    Raises ``ValueError`` for invalid input and ``ReviewRefused`` when the concern
    crosses the refusal boundary. On success returns the deterministic
    :class:`IntakeChecklist`; presentation is the caller's concern.
    """
    clean_concern_text = _screened_text(
        concern_text,
        top_k=top_k,
        evaluate_refusal=evaluate_refusal,
        blank_message="concern_text must not be blank",
    )

    return build_intake_checklist(clean_concern_text, top_k=top_k)


def run_retrieve(
    query_text: str,
    *,
    top_k: int = 5,
    source_type: str | None = SourceType.SOP.value,
    retrieve: Callable[..., list[SearchResult]] = default_retrieve,
    evaluate_refusal: Callable[[str], RefusalResult] = default_evaluate_refusal,
) -> list[SearchResult]:
    """Validate, screen against the refusal boundary, then retrieve evidence.

    Raises ``ValueError`` for invalid input and ``ReviewRefused`` when the query
    crosses the refusal boundary.
    """
    clean_query_text = _screened_text(
        query_text,
        top_k=top_k,
        evaluate_refusal=evaluate_refusal,
        blank_message="query_text must not be blank",
    )

    return retrieve(query=clean_query_text, top_k=top_k, source_type=source_type)


def run_final_assessment(
    concern_text: str,
    review_summary: ReviewSummary,
    *,
    top_k: int = 5,
    build_intake_checklist: Callable[..., IntakeChecklist] = default_build_intake_checklist,
    build_final_assessment: Callable[..., ExpectedStructuredOutput] = default_build_final_assessment,
    evaluate_refusal: Callable[[str], RefusalResult] = default_evaluate_refusal,
) -> ExpectedStructuredOutput:
    """Validate, screen against the refusal boundary, then build the final assessment.

    Rebuilds the checklist from the concern (the deterministic first phase) and
    combines it with the reviewer's ``review_summary`` to produce the final
    assessment. Raises ``ValueError`` for invalid input and ``ReviewRefused`` when
    the concern crosses the refusal boundary.
    """
    clean_concern_text = _screened_text(
        concern_text,
        top_k=top_k,
        evaluate_refusal=evaluate_refusal,
        blank_message="concern_text must not be blank",
    )

    checklist = build_intake_checklist(clean_concern_text, top_k=top_k)

    return build_final_assessment(
        checklist=checklist,
        review_summary=review_summary,
    )
