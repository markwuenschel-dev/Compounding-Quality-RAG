from __future__ import annotations

import json
import re
import sys
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import ValidationError

from app.checklist import build_intake_checklist
from app.checklist_models import EvidenceCitation, ChecklistItem, IntakeChecklist
from app.final_assessment import build_final_assessment
from app.llm_client import LLMClientError, openai_json_client_from_env
from app.refusal import evaluate_refusal
from app.review_summary_extraction import (
    ReviewSummaryExtractionError,
    extract_review_summary_result,
)
from app.retrieval import SearchResult, retrieve
from app.schemas import (
    ConcernType,
    RefusalResult,
    ReviewSummary,
    RiskLane,
    SourceType,
)


EXIT_SUCCESS = 0
EXIT_UNEXPECTED_FAILURE = 1

COMMAND_CHECKLIST = "checklist"
COMMAND_RETRIEVE = "retrieve"
COMMAND_FINAL_ASSESSMENT = "final_assessment"
COMMAND_EXTRACT_REVIEW_SUMMARY = "extract_review_summary"

CHECK_KEYS_BY_NAME = {
    "Record review": "record_review",
    "Lot or batch context review": "lot_batch_review",
    "Inventory inspection if available": "inventory_inspection",
    "Trend scan": "trend_scan",
    "Customer clinical context follow-up": "customer_context_follow_up",
    "Device administration context": "device_administration_context",
    "BUD field review": "bud_field_review",
}

_CAMEL_BOUNDARY_RE = re.compile(r"(?<!^)(?=[A-Z])")


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
            message="RAG engine failed while processing the request.",
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

    if command == COMMAND_RETRIEVE:
        return success_response(handle_retrieve(payload))

    if command == COMMAND_FINAL_ASSESSMENT:
        return success_response(handle_final_assessment(payload))

    if command == COMMAND_EXTRACT_REVIEW_SUMMARY:
        return success_response(handle_extract_review_summary(payload))

    raise BridgeRequestError(
        "UNKNOWN_COMMAND",
        f"Unsupported command: {command}",
    )


def handle_checklist(payload: dict[str, Any]) -> dict[str, Any]:
    concern_text = require_string(payload, "concernText", "payload.concernText")
    top_k = optional_positive_int(payload, "topK", "payload.topK", default=5)

    clean_text = require_non_blank_text(
        concern_text,
        "payload.concernText must not be blank",
    )

    enforce_refusal_boundary(clean_text)

    checklist = build_intake_checklist(clean_text, top_k=top_k)
    return checklist_to_api_result(checklist)


def handle_retrieve(payload: dict[str, Any]) -> dict[str, Any]:
    query_text = require_string(payload, "queryText", "payload.queryText")
    top_k = optional_positive_int(payload, "topK", "payload.topK", default=5)

    clean_text = require_non_blank_text(
        query_text,
        "payload.queryText must not be blank",
    )

    enforce_refusal_boundary(clean_text)

    search_results = retrieve(
        query=clean_text,
        top_k=top_k,
        source_type=SourceType.SOP.value,
    )

    return {
        "queryText": clean_text,
        "topK": top_k,
        "evidence": [
            search_result_to_api_item(result)
            for result in search_results
        ],
    }


def handle_final_assessment(payload: dict[str, Any]) -> dict[str, Any]:
    concern_text = require_string(payload, "concernText", "payload.concernText")
    top_k = optional_positive_int(payload, "topK", "payload.topK", default=5)
    review_summary_payload = require_object(
        payload,
        "reviewSummary",
        "payload.reviewSummary",
    )

    clean_text = require_non_blank_text(
        concern_text,
        "payload.concernText must not be blank",
    )

    enforce_refusal_boundary(clean_text)

    review_summary = review_summary_from_api_payload(review_summary_payload)
    checklist = build_intake_checklist(clean_text, top_k=top_k)

    final_assessment = build_final_assessment(
        checklist=checklist,
        review_summary=review_summary,
    )

    return convert_keys(
        final_assessment.model_dump(mode="json"),
        to_camel_case,
    )



def handle_extract_review_summary(payload: dict[str, Any]) -> dict[str, Any]:
    concern_text = require_string(
        payload,
        "concernText",
        "payload.concernText",
    )
    pharmacist_notes = require_string(
        payload,
        "pharmacistNotes",
        "payload.pharmacistNotes",
    )

    clean_concern_text = require_non_blank_text(
        concern_text,
        "payload.concernText must not be blank",
    )
    clean_pharmacist_notes = require_non_blank_text(
        pharmacist_notes,
        "payload.pharmacistNotes must not be blank",
    )

    enforce_refusal_boundary(clean_concern_text)

    try:
        result = extract_review_summary_result(
            reviewer_note=clean_pharmacist_notes,
            llm_client=openai_json_client_from_env(),
            concern_text=clean_concern_text,
        )
    except (ReviewSummaryExtractionError, LLMClientError) as exc:
        raise BridgeRequestError(
            "EXTRACTION_FAILURE",
            str(exc),
        ) from exc

    return convert_keys(
        result.model_dump(mode="json"),
        to_camel_case,
    )

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


def search_result_to_api_item(result: SearchResult) -> dict[str, Any]:
    chunk = result["chunk"]

    return {
        "chunkId": chunk["chunk_id"],
        "sourceId": chunk["source_id"],
        "sourceTitle": chunk["source_title"],
        "sourceType": chunk["source_type"],
        "sectionHeading": chunk["section_heading"],
        "score": float(result["score"]),
        "matchedTerms": list(result["matched_terms"]),
        "supportingText": chunk["text"],
    }


def review_summary_from_api_payload(payload: dict[str, Any]) -> ReviewSummary:
    snake_case_payload = convert_keys(payload, to_snake_case)

    try:
        return ReviewSummary.model_validate(snake_case_payload)
    except ValidationError as exc:
        raise BridgeRequestError(
            "INVALID_REQUEST",
            "payload.reviewSummary did not match the review summary contract",
            details={
                "errors": exc.errors(include_url=False),
            },
        ) from exc


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


def enforce_refusal_boundary(text: str) -> None:
    refusal = evaluate_refusal(text)

    if refusal.refused:
        raise refusal_error(refusal)


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


def require_non_blank_text(value: str, message: str) -> str:
    clean_value = value.strip()

    if not clean_value:
        raise BridgeRequestError(
            "INVALID_REQUEST",
            message,
        )

    return clean_value


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


def convert_keys(
    value: Any,
    key_converter: Callable[[str], str],
) -> Any:
    if isinstance(value, dict):
        return {
            key_converter(str(key)): convert_keys(item, key_converter)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            convert_keys(item, key_converter)
            for item in value
        ]

    return value


def to_snake_case(value: str) -> str:
    return _CAMEL_BOUNDARY_RE.sub("_", value).lower()


def to_camel_case(value: str) -> str:
    parts = value.split("_")

    if len(parts) == 1:
        return value

    return parts[0] + "".join(part.capitalize() for part in parts[1:])


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
