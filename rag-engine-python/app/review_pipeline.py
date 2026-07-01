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
from app.refusal import evaluate_refusal as default_evaluate_refusal
from app.schemas import RefusalResult


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
    clean_concern_text = concern_text.strip()
    if not clean_concern_text:
        raise ValueError("concern_text must not be blank")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    refusal = evaluate_refusal(clean_concern_text)
    if refusal.refused:
        raise ReviewRefused(refusal)

    return build_intake_checklist(clean_concern_text, top_k=top_k)
