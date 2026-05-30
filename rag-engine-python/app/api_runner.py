from __future__ import annotations

import json
import re
import sys
import traceback
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.checklist import build_intake_checklist
from app.checklist_models import EvidenceCitation, ChecklistItem, IntakeChecklist
from app.refusal import evaluate_refusal
from app.schemas import ConcernType, RefusalResult, RiskLane


EXIT_SUCCESS = 0
EXIT_UNEXPECTED_FAILURE = 1

COMMAND_CHECKLIST = "checklist"

CHECK_KEYS_BY_NAME = {
    "Record review": "record_review",
    "Lot or batch context review": "lot_batch_review",
    "Inventory inspection if available": "inventory_inspection",
    "Trend scan": "trend_scan",
    "Customer clinical context follow-up": "customer_context_follow_up",
    "Device administration context": "device_administration_context",
    "BUD field review": "bud_field_review",
}


@dataclass(frozen=True)
class BridgeResult:
    stdout: str
    stderr: str
    exit_code: int


class BridgeRequestError(Exception):
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


def main() -> int:
    result = run_bridge(sys.stdin.read())

    if result.stdout:
        sys.stdout.write(result.stdout)
        sys.stdout.write("\n")

    if result.stderr:
        sys.stderr.write(result.stderr)
        if not result.stderr.endswith("\n"):
            sys.stderr.write("\n")

    return result.exit_code


def run_bridge(raw_input: str) -> BridgeResult:
    try:
        response = handle_request(raw_input)
        return BridgeResult(
            stdout=encode_response(response),
            stderr="",
            exit_code=EXIT_SUCCESS,
        )
    except BridgeRequestError as exc:
        response = error_response(
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )
        return BridgeResult(
            stdout=encode_response(response),
            stderr="",
            exit_code=EXIT_SUCCESS,
        )
    except Exception:
        response = error_response(
            code="ENGINE_FAILURE",
            message="Checklist engine failed while processing the request.",
        )
        return BridgeResult(
            stdout=encode_response(response),
            stderr=traceback.format_exc(),
            exit_code=EXIT_UNEXPECTED_FAILURE,
        )


def handle_request(raw_input: str) -> dict[str, Any]:
    request = parse_json_object(raw_input)

    command = require_string(request, "command", "command")
    payload = require_object(request, "payload", "payload")

    if command == COMMAND_CHECKLIST:
        return success_response(handle_checklist(payload))

    raise BridgeRequestError(
        "UNKNOWN_COMMAND",
        f"Unsupported command: {command}",
    )


def handle_checklist(payload: dict[str, Any]) -> dict[str, Any]:
    concern_text = require_string(payload, "concernText", "payload.concernText")
    top_k = optional_positive_int(payload, "topK", "payload.topK", default=5)

    clean_text = concern_text.strip()
    if not clean_text:
        raise BridgeRequestError(
            "INVALID_REQUEST",
            "payload.concernText must not be blank",
        )

    refusal = evaluate_refusal(clean_text)
    if refusal.refused:
        raise refusal_error(refusal)

    checklist = build_intake_checklist(clean_text, top_k=top_k)
    return checklist_to_api_result(checklist)


def checklist_to_api_result(checklist: IntakeChecklist) -> dict[str, Any]:
    return {
        "concernType": enum_value_or_none(checklist.likely_concern_type),
        "riskLane": enum_value_or_none(checklist.likely_risk_lane),
        "reviewScope": derive_review_scope(checklist),
        "initialTakeaway": build_initial_takeaway(checklist),
        "requiredChecks": [
            checklist_item_to_api_item(item)
            for item in checklist.review_checks
        ],
        "missingInformation": list(checklist.missing_information),
        "escalationTriggersToRuleOut": [
            trigger.value
            for trigger in checklist.escalation_triggers_to_rule_out
        ],
        "evidence": [
            evidence_to_api_item(citation)
            for citation in checklist.evidence
        ],
        "limitations": list(checklist.limitations),
    }


def checklist_item_to_api_item(item: ChecklistItem) -> dict[str, Any]:
    return {
        "key": CHECK_KEYS_BY_NAME.get(item.check_name, slugify(item.check_name)),
        "label": item.check_name,
        "required": item.required,
        "reason": item.rationale,
    }


def evidence_to_api_item(citation: EvidenceCitation) -> dict[str, Any]:
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


def refusal_error(refusal: RefusalResult) -> BridgeRequestError:
    details: dict[str, Any] = {
        "reason": refusal.reason.value if refusal.reason is not None else None,
        "matchedTerms": list(refusal.matched_terms),
    }

    return BridgeRequestError(
        "REFUSED",
        refusal.message or "Request was refused by review boundary rules.",
        details=details,
    )


def parse_json_object(raw_input: str) -> dict[str, Any]:
    if not raw_input.strip():
        raise BridgeRequestError(
            "INVALID_JSON",
            "stdin must contain a JSON request object",
        )

    try:
        parsed = json.loads(raw_input)
    except json.JSONDecodeError as exc:
        raise BridgeRequestError(
            "INVALID_JSON",
            f"Invalid JSON: {exc.msg}",
        ) from exc

    if not isinstance(parsed, dict):
        raise BridgeRequestError(
            "INVALID_REQUEST",
            "request body must be a JSON object",
        )

    return parsed


def require_object(
    source: dict[str, Any],
    field_name: str,
    field_path: str,
) -> dict[str, Any]:
    value = source.get(field_name)

    if not isinstance(value, dict):
        raise BridgeRequestError(
            "INVALID_REQUEST",
            f"{field_path} must be a JSON object",
        )

    return value


def require_string(
    source: dict[str, Any],
    field_name: str,
    field_path: str,
) -> str:
    value = source.get(field_name)

    if not isinstance(value, str):
        raise BridgeRequestError(
            "INVALID_REQUEST",
            f"{field_path} must be a string",
        )

    return value


def optional_positive_int(
    source: dict[str, Any],
    field_name: str,
    field_path: str,
    *,
    default: int,
) -> int:
    if field_name not in source:
        return default

    value = source[field_name]

    if not isinstance(value, int) or isinstance(value, bool):
        raise BridgeRequestError(
            "INVALID_REQUEST",
            f"{field_path} must be an integer",
        )

    if value < 1:
        raise BridgeRequestError(
            "INVALID_REQUEST",
            f"{field_path} must be at least 1",
        )

    return value


def success_response(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "result": result,
    }


def error_response(
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {
        "code": code,
        "message": message,
    }

    if details:
        error["details"] = details

    return {
        "ok": False,
        "error": error,
    }


def encode_response(response: dict[str, Any]) -> str:
    return json.dumps(response, ensure_ascii=False, separators=(",", ":"))


def enum_value_or_none(value: Enum | None) -> str | None:
    if value is None:
        return None

    return str(value.value)


def humanize_enum(value: Enum | None) -> str:
    if value is None:
        return "unknown"

    return str(value.value).replace("_", " ")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")

    if not slug:
        return "check"

    return slug


if __name__ == "__main__":
    raise SystemExit(main())