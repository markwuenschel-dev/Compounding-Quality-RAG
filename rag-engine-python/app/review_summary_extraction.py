from __future__ import annotations

import json
import re
from collections.abc import Iterable
from enum import StrEnum
from typing import Any, Protocol

from pydantic import ValidationError

from app.schemas import (
    ApiReferenceReviewResult,
    EscalationTrigger,
    InventoryInspectionResult,
    LotBatchPatternSummary,
    RecordReviewResult,
    ReviewSummary,
)


class LLMClient(Protocol):
    def complete_json(self, prompt: str) -> str:
        ...


class ReviewSummaryExtractionError(ValueError):
    pass


class ReviewSummaryGroundingError(ReviewSummaryExtractionError):
    pass


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL)
_SPACE_RE = re.compile(r"[\s\-_]+")

_LIST_FIELDS = {
    "missing_information",
    "evidence_limitations",
    "severe_triggers_observed",
}

_ENUM_FIELDS: dict[str, type[StrEnum]] = {
    "record_review_result": RecordReviewResult,
    "lot_batch_pattern_summary": LotBatchPatternSummary,
    "inventory_inspection_result": InventoryInspectionResult,
    "api_reference_review_result": ApiReferenceReviewResult,
}

_TRIGGER_TERMS: dict[EscalationTrigger, tuple[str, ...]] = {
    EscalationTrigger.PET_DEATH: (
        "death",
        "died",
        "dead",
        "passed away",
        "euthanized",
    ),
    EscalationTrigger.PET_HOSPITALIZATION: (
        "hospitalized",
        "hospitalization",
        "hospitalised",
        "hospitalisation",
        "emergency hospital",
        "er visit",
        "emergency vet",
    ),
    EscalationTrigger.THREATENED_LEGAL_ACTION: (
        "legal threat",
        "legal action",
        "lawsuit",
        "lawyer",
        "attorney",
        "liable",
        "liability",
    ),
    EscalationTrigger.VETERINARIAN_ALLEGES_HARM_FROM_COMPOUND: (
        "vet alleged",
        "veterinarian alleged",
        "vet said the compound caused",
        "veterinarian said the compound caused",
        "vet blamed",
        "veterinarian blamed",
        "vet alleges",
        "veterinarian alleges",
    ),
    EscalationTrigger.POSSIBLE_CONTAMINATION: (
        "contamination",
        "contaminated",
        "foreign material",
        "mold",
        "particulate",
    ),
    EscalationTrigger.WRONG_PATIENT_OR_WRONG_MEDICATION: (
        "wrong medication",
        "wrong med",
        "wrong patient",
        "different patient",
        "dispensing error",
    ),
    EscalationTrigger.REPEAT_ISSUE_SAME_LOT_OR_BATCH_WITH_CONDITIONS: (
        "same lot",
        "same batch",
        "repeat issue",
        "similar complaints",
        "trend threshold",
    ),
    EscalationTrigger.RARE_REGULATORY_OR_COMPLIANCE_CONCERN: (
        "regulatory",
        "compliance concern",
        "board of pharmacy",
        "state board",
    ),
}

_NEGATION_RE = re.compile(
    r"\b(no|not|none|without|denied|denies|deny|negative for|no evidence of|no report of|not reported|wasn't|weren't|isn't|aren't)\b",
    re.IGNORECASE,
)

_AFFIRMATION_RE = re.compile(
    r"\b(confirmed|observed|reported|found|identified|documented|present|occurred|was|were|is|had|has)\b",
    re.IGNORECASE,
)

_INVENTORY_UNAVAILABLE_RE = re.compile(
    r"\b(no inventory available|inventory (?:was )?(?:not available|unavailable)|not available to inspect|unavailable to inspect)\b",
    re.IGNORECASE,
)

_INVENTORY_NOT_CHECKED_RE = re.compile(
    r"\b(inventory (?:was )?(?:not checked|not inspected)|not physically inspected|not inspected by this tool|device was not physically inspected)\b",
    re.IGNORECASE,
)

_EXTERNAL_UNSUPPORTED_RE = re.compile(
    r"\b(plumb'?s?|external (?:drug )?reference|drug handbook|package insert)\b.*\b(not supported|not available|public corpus|synthetic corpus|cannot support|unavailable)\b"
    r"|\b(not supported|not available|public corpus|synthetic corpus|cannot support|unavailable)\b.*\b(plumb'?s?|external (?:drug )?reference|drug handbook|package insert)\b",
    re.IGNORECASE | re.DOTALL,
)

_EXTERNAL_NEEDED_RE = re.compile(
    r"\b(external (?:drug )?reference needed|plumb'?s? needed|package insert needed|drug handbook needed)\b",
    re.IGNORECASE,
)

_SYNTHETIC_REFERENCE_RE = re.compile(
    r"\b(synthetic reference consulted|synthetic api reference consulted|public synthetic reference consulted)\b",
    re.IGNORECASE,
)

_NO_SEVERE_TRIGGER_RE = re.compile(
    r"\b(no severe escalation trigger|no severe trigger|no escalation trigger|no structured severe trigger|reviewer observed no severe)\b",
    re.IGNORECASE,
)


# This boundary deliberately accepts only a small client protocol. Provider-specific SDK
# calls belong in a separate adapter so tests can prove schema behavior without network I/O.
def extract_review_summary(reviewer_note: str, llm_client: LLMClient) -> ReviewSummary:
    clean_note = reviewer_note.strip()
    if not clean_note:
        raise ValueError("reviewer_note must not be empty")

    raw_response = llm_client.complete_json(build_review_summary_prompt(clean_note))
    payload = parse_llm_json(raw_response)
    normalized_payload = normalize_review_summary_payload(payload)

    try:
        summary = ReviewSummary.model_validate(normalized_payload)
    except ValidationError as exc:
        raise ReviewSummaryExtractionError(
            "LLM response did not match ReviewSummary."
        ) from exc

    return enforce_review_summary_grounding(summary, clean_note)


def build_review_summary_prompt(reviewer_note: str) -> str:
    return f"""
You extract structured pharmacy quality review findings from reviewer notes.

Return ONLY valid JSON. Do not include markdown or explanatory text.
Use only facts stated in the reviewer note. Do not infer clinical causality.
Do not invent record findings, batch trends, inventory findings, external-reference findings, or severe triggers.

Required JSON object:
{{
  "record_review_result": one of {enum_values(RecordReviewResult)},
  "lot_batch_pattern_summary": one of {enum_values(LotBatchPatternSummary)},
  "inventory_inspection_result": one of {enum_values(InventoryInspectionResult)},
  "customer_context_summary": string or null,
  "api_reference_review_result": one of {enum_values(ApiReferenceReviewResult)},
  "missing_information": list of strings,
  "evidence_limitations": list of strings,
  "severe_triggers_observed": list containing only values from {enum_values(EscalationTrigger)}
}}

Safety rules:
- If a note says no hospitalization, no death, no legal threat, no contamination, no wrong medication, or no veterinarian allegation, do not include that severe trigger.
- Only include a severe trigger when the reviewer affirmatively confirms it.
- "Severity unknown" is not a severe trigger.
- "Possible wrong medication" or "possible wrong patient" is a severe trigger only when the reviewer confirms the issue is possible or documented, not when they say it was ruled out.
- If inventory was unavailable, use "no_inventory_available" and add that limitation.
- If inventory was not checked or not inspected, use "not_checked".
- If lot/batch trend information was unavailable, use "unavailable".
- If a field is irrelevant to the case, use "not_applicable".
- If no external/API reference was needed, use "not_needed".
- If external references are outside the public synthetic corpus, use "not_supported_by_public_corpus" and add an evidence limitation.
- Keep missing_information and evidence_limitations as concise, reviewer-facing strings.

Reviewer note:
{reviewer_note}
""".strip()


def parse_llm_json(raw_response: str) -> dict[str, Any]:
    clean_response = raw_response.strip()
    if not clean_response:
        raise ReviewSummaryExtractionError("LLM response was empty.")

    fenced_match = _JSON_FENCE_RE.search(clean_response)
    if fenced_match:
        clean_response = fenced_match.group(1).strip()

    try:
        payload = json.loads(clean_response)
    except json.JSONDecodeError:
        payload = json.loads(extract_first_json_object(clean_response))

    if not isinstance(payload, dict):
        raise ReviewSummaryExtractionError("LLM response JSON must be an object.")

    return payload


def extract_first_json_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        raise ReviewSummaryExtractionError("LLM response did not contain a JSON object.")

    depth = 0
    in_string = False
    escaped = False

    for index in range(start, len(text)):
        char = text[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]

    raise ReviewSummaryExtractionError("LLM response contained an incomplete JSON object.")


def normalize_review_summary_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)

    for field_name, enum_cls in _ENUM_FIELDS.items():
        if field_name in normalized:
            normalized[field_name] = normalize_enum_value(normalized[field_name], enum_cls)

    if "severe_triggers_observed" in normalized:
        normalized["severe_triggers_observed"] = [
            normalize_enum_value(value, EscalationTrigger)
            for value in normalize_string_list(normalized["severe_triggers_observed"])
        ]

    for field_name in _LIST_FIELDS - {"severe_triggers_observed"}:
        if field_name in normalized:
            normalized[field_name] = normalize_string_list(normalized[field_name])

    if normalized.get("customer_context_summary") == "":
        normalized["customer_context_summary"] = None

    return normalized


def normalize_enum_value(value: Any, enum_cls: type[StrEnum]) -> Any:
    if isinstance(value, enum_cls):
        return value.value

    if not isinstance(value, str):
        return value

    normalized_value = normalize_token(value)
    for member in enum_cls:
        if normalized_value in {normalize_token(member.value), normalize_token(member.name)}:
            return member.value

    return value


def normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        clean_value = value.strip()
        if clean_value.lower() in {"", "none", "n/a", "na", "not applicable", "[]"}:
            return []
        return [clean_value]

    if not isinstance(value, list):
        return value

    output: list[str] = []
    for item in value:
        if item is None:
            continue
        clean_item = str(item).strip()
        if clean_item and clean_item.lower() not in {"none", "n/a", "na", "not applicable"}:
            output.append(clean_item)

    return unique_in_order(output)


def enforce_review_summary_grounding(
    summary: ReviewSummary,
    reviewer_note: str,
) -> ReviewSummary:
    data = summary.model_dump(mode="json")
    note = reviewer_note.strip()

    data["missing_information"] = unique_in_order(data["missing_information"])
    data["evidence_limitations"] = unique_in_order(data["evidence_limitations"])
    data["severe_triggers_observed"] = infer_grounded_severe_triggers(
        note,
        data["severe_triggers_observed"],
    )

    apply_inventory_grounding(note, data)
    apply_api_reference_grounding(note, data)

    try:
        return ReviewSummary.model_validate(data)
    except ValidationError as exc:
        raise ReviewSummaryGroundingError(
            "Post-processed ReviewSummary no longer matched the schema."
        ) from exc


def infer_grounded_severe_triggers(
    reviewer_note: str,
    model_triggers: Iterable[str],
) -> list[str]:
    model_trigger_values = {
        normalize_enum_value(trigger, EscalationTrigger)
        for trigger in model_triggers
    }
    grounded: set[str] = set()

    for trigger in EscalationTrigger:
        if trigger_is_affirmed(reviewer_note, trigger):
            grounded.add(trigger.value)

    if _NO_SEVERE_TRIGGER_RE.search(reviewer_note) and not grounded:
        return []

    for trigger_value in model_trigger_values:
        try:
            trigger = EscalationTrigger(trigger_value)
        except ValueError:
            continue

        if trigger.value in grounded:
            continue

        if trigger_is_negated(reviewer_note, trigger):
            continue

        if trigger_is_affirmed(reviewer_note, trigger):
            grounded.add(trigger.value)

    return sorted(grounded)


def trigger_is_affirmed(text: str, trigger: EscalationTrigger) -> bool:
    for sentence in split_sentences(text):
        if not contains_trigger_term(sentence, trigger):
            continue

        if sentence_negates_trigger(sentence, trigger):
            continue

        if _AFFIRMATION_RE.search(sentence):
            return True

    return False


def trigger_is_negated(text: str, trigger: EscalationTrigger) -> bool:
    if _NO_SEVERE_TRIGGER_RE.search(text):
        return True
    return any(
        contains_trigger_term(sentence, trigger) and sentence_negates_trigger(sentence, trigger)
        for sentence in split_sentences(text)
    )


def sentence_negates_trigger(sentence: str, trigger: EscalationTrigger) -> bool:
    lowered = sentence.lower()
    terms = _TRIGGER_TERMS[trigger]

    for term in terms:
        term_index = lowered.find(term)
        if term_index < 0:
            continue

        prefix = lowered[:term_index]
        local_prefix = lowered[max(0, term_index - 90):term_index]
        suffix = lowered[term_index:term_index + len(term) + 45]

        if re.search(r"\bruled out\b", suffix, re.IGNORECASE):
            return True

        if _NEGATION_RE.search(local_prefix):
            return True

        if coordinated_negation_applies(prefix):
            return True

    return False

def coordinated_negation_applies(prefix: str) -> bool:
    normalized = prefix.lower()

    if re.search(r"\b(no|without)\b", normalized):
        return True

    if re.search(r"\bnot\s+(?:confirmed|observed|reported|found|identified|documented)\b", normalized):
        return True

    if re.search(r"\bhas\s+not\s+(?:confirmed|observed|reported|found|identified|documented)\b", normalized):
        return True

    if re.search(r"\bwas\s+not\s+(?:confirmed|observed|reported|found|identified|documented)\b", normalized):
        return True

    return False

def contains_trigger_term(sentence: str, trigger: EscalationTrigger) -> bool:
    lowered = sentence.lower()
    return any(term in lowered for term in _TRIGGER_TERMS[trigger])


def split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[.;\n]+", text) if part.strip()]


def apply_inventory_grounding(note: str, data: dict[str, Any]) -> None:
    if _INVENTORY_UNAVAILABLE_RE.search(note):
        data["inventory_inspection_result"] = InventoryInspectionResult.NO_INVENTORY_AVAILABLE.value
        add_unique(
            data["evidence_limitations"],
            "Inventory was not available to inspect.",
        )
        return

    if _INVENTORY_NOT_CHECKED_RE.search(note):
        data["inventory_inspection_result"] = InventoryInspectionResult.NOT_CHECKED.value
        add_unique(
            data["evidence_limitations"],
            "Inventory was not inspected.",
        )


def apply_api_reference_grounding(note: str, data: dict[str, Any]) -> None:
    if _EXTERNAL_UNSUPPORTED_RE.search(note):
        data["api_reference_review_result"] = ApiReferenceReviewResult.NOT_SUPPORTED_BY_PUBLIC_CORPUS.value
        add_unique(
            data["evidence_limitations"],
            "External drug-reference information was not supported by the public synthetic corpus.",
        )
        return

    if _EXTERNAL_NEEDED_RE.search(note):
        data["api_reference_review_result"] = ApiReferenceReviewResult.EXTERNAL_REFERENCE_NEEDED.value
        return

    if _SYNTHETIC_REFERENCE_RE.search(note):
        data["api_reference_review_result"] = ApiReferenceReviewResult.SYNTHETIC_REFERENCE_CONSULTED.value


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_cls]


def normalize_token(value: str) -> str:
    return _SPACE_RE.sub("_", value.strip().lower())


def add_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def unique_in_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []

    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)

    return output
