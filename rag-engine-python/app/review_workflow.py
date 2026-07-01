from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.checklist import build_intake_checklist as default_build_intake_checklist
from app.checklist_models import EvidenceCitation, ChecklistItem, IntakeChecklist
from app.review_pipeline import ReviewRefused, run_checklist as run_checklist_pipeline
from app.schemas import ConcernType, RiskLane


CHECK_KEYS_BY_NAME = {
    "Record review": "record_review",
    "Lot or batch context review": "lot_batch_review",
    "Inventory inspection if available": "inventory_inspection",
    "Trend scan": "trend_scan",
    "Customer clinical context follow-up": "customer_context_follow_up",
    "Device administration context": "device_administration_context",
    "BUD field review": "bud_field_review",
}


class WorkflowRequestError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


@dataclass(frozen=True)
class ChecklistWorkflowRequest:
    concern_text: str
    top_k: int = 5


class ReviewWorkflow:
    def __init__(
        self,
        *,
        build_intake_checklist: Callable[..., IntakeChecklist] = default_build_intake_checklist,
    ) -> None:
        self._build_intake_checklist = build_intake_checklist

    def run_checklist(
        self,
        request: ChecklistWorkflowRequest,
    ) -> dict[str, Any]:
        try:
            checklist = run_checklist_pipeline(
                request.concern_text,
                top_k=request.top_k,
                build_intake_checklist=self._build_intake_checklist,
            )
        except ReviewRefused as exc:
            refusal = exc.refusal
            raise WorkflowRequestError(
                "REFUSED",
                refusal.message or "Request was refused by review boundary rules.",
                details={
                    "reason": (
                        refusal.reason.value
                        if refusal.reason is not None
                        else None
                    ),
                    "matchedTerms": list(refusal.matched_terms),
                },
            ) from exc
        except ValueError as exc:
            raise WorkflowRequestError(
                "INVALID_REQUEST",
                str(exc),
            ) from exc

        return checklist_to_review_contract(checklist)


def checklist_to_review_contract(checklist: IntakeChecklist) -> dict[str, Any]:
    return {
        "concernType": enum_value_or_none(checklist.likely_concern_type),
        "riskLane": enum_value_or_none(checklist.likely_risk_lane),
        "reviewScope": derive_review_scope(checklist),
        "initialTakeaway": build_initial_takeaway(checklist),
        "requiredChecks": [
            checklist_item_to_review_contract(item)
            for item in checklist.review_checks
        ],
        "missingInformation": list(checklist.missing_information),
        "escalationTriggersToRuleOut": [
            trigger.value
            for trigger in checklist.escalation_triggers_to_rule_out
        ],
        "evidence": [
            evidence_to_review_contract(citation)
            for citation in checklist.evidence
        ],
        "limitations": list(checklist.limitations),
    }


def checklist_item_to_review_contract(item: ChecklistItem) -> dict[str, Any]:
    return {
        "key": CHECK_KEYS_BY_NAME.get(item.check_name, slugify(item.check_name)),
        "label": item.check_name,
        "required": item.required,
        "reason": item.rationale,
    }


def evidence_to_review_contract(citation: EvidenceCitation) -> dict[str, Any]:
    return {
        "chunkId": citation.chunk_id,
        "sourceId": citation.source_id,
        "sourceTitle": citation.source_title,
        "sourceType": citation.source_type,
        "sectionHeading": citation.section_heading,
        "score": citation.score,
        "matchedTerms": list(citation.matched_terms),
        "supportingText": citation.supporting_text,
    }


def derive_review_scope(checklist: IntakeChecklist) -> str:
    if checklist.likely_risk_lane == RiskLane.LIFE_THREATENING_OR_LEGAL:
        return "escalation_review"

    if checklist.likely_concern_type == ConcernType.BUD_QUESTION:
        return "guidance_only"

    return "full_quality_review"


def build_initial_takeaway(checklist: IntakeChecklist) -> str:
    concern_type = humanize_enum(checklist.likely_concern_type)
    risk_lane = humanize_enum(checklist.likely_risk_lane)

    return (
        f"Initial screen suggests {concern_type} with {risk_lane} risk lane. "
        "Final routing depends on review findings and confirmed escalation triggers."
    )


def enum_value_or_none(value: object) -> str | None:
    if value is None:
        return None

    enum_value = getattr(value, "value", value)
    return str(enum_value)


def humanize_enum(value: object) -> str:
    enum_value = enum_value_or_none(value)

    if enum_value is None:
        return "unknown"

    return enum_value.replace("_", " ")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")

    return slug or "check"
