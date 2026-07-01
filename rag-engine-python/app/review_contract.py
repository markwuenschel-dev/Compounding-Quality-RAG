"""Presenter for the review bridge: maps a domain IntakeChecklist to the contract.

Presentation only. It shapes the pipeline's domain result (`IntakeChecklist`) into the
camelCase dict the stdin bridge returns to callers. Orchestration and the refusal
boundary live in :mod:`app.review_pipeline`, not here.
"""

from __future__ import annotations

import re
from typing import Any

from app.checklist_models import EvidenceCitation, ChecklistItem, IntakeChecklist
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
