from __future__ import annotations

import json
import re
from collections.abc import Iterable
from enum import StrEnum
from typing import Any, Protocol

from pydantic import ValidationError

from app.contextual_missing_information import build_decision_relevant_questions
from app.schemas import (
    ApiReferenceReviewResult,
    ExtractionEvidenceStatus,
    EscalationTrigger,
    InventoryInspectionResult,
    LotBatchPatternSummary,
    RecordReviewResult,
    ReviewSummaryExtractionResult,
    ReviewSummaryFieldEvidence,
    ReviewSummary,
)
from app.review_summary_policy import apply_review_summary_defaults


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
    r"\b(no inventory available|no inventory left(?: to inspect)?|inventory (?:was )?(?:not available|unavailable)|not available to inspect|unavailable to inspect)\b",
    re.IGNORECASE,
)

_INVENTORY_NOT_CHECKED_RE = re.compile(
    r"\b(inventory (?:was )?(?:not checked|not inspected)|not physically inspected|not inspected by this tool|device was not physically inspected)\b",
    re.IGNORECASE,
)

_EXTERNAL_UNSUPPORTED_RE = re.compile(
    r"\b(plumb'?s?|external (?:drug )?reference|drug handbook|package insert)\b[^.\n;]{0,160}\b(not supported|not available|public corpus|synthetic corpus|cannot support|unavailable)\b"
    r"|\b(not supported|not available|public corpus|synthetic corpus|cannot support|unavailable)\b[^.\n;]{0,160}\b(plumb'?s?|external (?:drug )?reference|drug handbook|package insert)\b",
    re.IGNORECASE,
)

_EXTERNAL_NEEDED_RE = re.compile(
    r"\b(external (?:drug )?reference needed|plumb'?s? needed|package insert needed|drug handbook needed)\b",
    re.IGNORECASE,
)

_EXTERNAL_CONSULTED_RE = re.compile(
    r"\b(?:the\s+)?assessment\s+incorporated\s+[^.\n;]{0,160}"
    r"\b(?:usp guidance|manufacturer information|internal clinical guidance|"
    r"(?:a\s+)?veterinary drug reference|(?:the\s+)?commercial package insert)\b"
    r"|\b(?:consulted|reviewed|used)\s+[^.\n;]{0,80}"
    r"\b(?:usp guidance|manufacturer information|internal clinical guidance|"
    r"(?:a\s+)?veterinary drug reference|(?:the\s+)?commercial package insert|"
    r"external (?:drug )?reference)\b",
    re.IGNORECASE,
)

_NON_DISCLOSURE_RE = re.compile(
    r"\b(?:specific\s+)?(?:supplier|manufacturer)(?:\s+or\s+manufacturer)?"
    r"\s+(?:details?|identity|information)\s+(?:were|was|cannot be|could not be)"
    r"\s+(?:not\s+)?disclosed\b"
    r"|\bfull\s+proprietary\s+(?:formula|formulation|ingredient list)"
    r"\s+(?:was|were|cannot be|could not be)\s+(?:not\s+)?disclosed\b"
    r"|\b(?:cannot|can not|could not|unable to)\s+disclose\s+"
    r"(?:the\s+)?(?:supplier|manufacturer|full proprietary formula|"
    r"full ingredient list)\b",
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


_RECORD_DISCREPANCY_RE = re.compile(
    r"\b(?:documentation discrepancy|record discrepancy|worksheet discrepancy|formula discrepancy|wrong patient|wrong medication|different patient|different medication|label was for a different patient)\b",
    re.IGNORECASE,
)

_RECORD_INCOMPLETE_RE = re.compile(
    r"\b(?:documentation incomplete|record incomplete|worksheet incomplete|missing documentation|incomplete documentation)\b",
    re.IGNORECASE,
)

_RECORD_NO_DISCREPANCY_RE = re.compile(
    r"\b(?:no discrepancy|nothing off|record review (?:was )?(?:normal|complete)|worksheet review (?:was )?(?:normal|complete)|formula review (?:was )?(?:normal|complete)|correct medication and patient|correct patient and medication)\b",
    re.IGNORECASE,
)

_RECORD_NOT_APPLICABLE_RE = re.compile(
    r"\b(?:record review|documentation review|worksheet review)\s+(?:was\s+)?not applicable\b",
    re.IGNORECASE,
)

_LOT_NOT_APPLICABLE_RE = re.compile(
    r"\b(?:lot|batch|lot review|batch review|lot trend|batch trend)\s+(?:was\s+)?not applicable\b",
    re.IGNORECASE,
)

_LOT_UNAVAILABLE_RE = re.compile(
    r"\b(?:lot|batch|lot trend|batch trend|lot review|batch review)\s+(?:was\s+)?(?:unavailable|not available|unknown|not known)\b",
    re.IGNORECASE,
)

_LOT_NO_SIMILAR_RE = re.compile(
    r"\b(?:same\s+)?(?:lot|batch)[^.\n;]{0,80}\bno\s+similar\s+(?:complaints?|concerns?|issues?)\b"
    r"|\bno\s+similar\s+(?:complaints?|concerns?|issues?)[^.\n;]{0,80}\b(?:lot|batch)\b"
    r"|\bno\s+similar\s+(?:lot|batch)\s+(?:complaints?|concerns?|issues?)\b",
    re.IGNORECASE,
)

_LOT_SAME_BATCH_FOUND_RE = re.compile(
    r"\b(?:similar|repeat)\s+(?:complaint|concern|issue)s?\s+(?:was\s+|were\s+)?(?:found|identified|confirmed)[^.\n;]{0,60}\b(?:same\s+)?(?:lot|batch)\b"
    r"|\b(?:same\s+)?(?:lot|batch)[^.\n;]{0,60}\b(?:similar|repeat)\s+(?:complaint|concern|issue)s?\s+(?:was\s+|were\s+)?(?:found|identified|confirmed)\b",
    re.IGNORECASE,
)

_LOT_SAME_PRODUCT_FOUND_RE = re.compile(
    r"\bsimilar\s+(?:complaint|concern|issue)s?\s+(?:was\s+|were\s+)?(?:found|identified|confirmed)[^.\n;]{0,80}\b(?:same medication|same dosage form|same product)\b",
    re.IGNORECASE,
)

_LOT_TREND_THRESHOLD_RE = re.compile(
    r"\btrend threshold (?:was\s+)?(?:met|reached|exceeded)\b",
    re.IGNORECASE,
)

_INVENTORY_NOT_APPLICABLE_RE = re.compile(
    r"\b(?:inventory inspection|inventory review|inventory)\s+(?:was\s+)?not applicable\b",
    re.IGNORECASE,
)

_INVENTORY_NO_VISUAL_RE = re.compile(
    r"\b(?:no visual concern|no visible concern|no defect observed|no visible defect|inspection found no concern|inventory inspection found no visual concern)\b",
    re.IGNORECASE,
)

_INVENTORY_VISUAL_CONCERN_RE = re.compile(
    r"\b(?:visual concern found|visible concern found|visual defect found|visible defect found|inspection found a concern|foreign material observed|particulate observed|mold observed)\b",
    re.IGNORECASE,
)

_API_NOT_NEEDED_RE = re.compile(
    r"\b(?:external|api|drug)?\s*reference\s+(?:was\s+)?not needed\b"
    r"|\bno external reference (?:was\s+)?needed\b",
    re.IGNORECASE,
)

_EXPLICIT_DOSE_MISSING_RE = re.compile(
    r"\b(?:exact\s+)?dose\s+(?:is\s+|was\s+)?(?:unknown|not known|not documented|missing|still unknown)\b"
    r"|\b(?:still need|need to confirm|could not confirm|couldn't confirm)\s+(?:the\s+)?(?:exact\s+)?dose\b",
    re.IGNORECASE,
)

_EXPLICIT_DEVICE_DISPENSE_MISSING_RE = re.compile(
    r"\b(?:could not confirm|couldn't confirm|unable to confirm|not sure|unknown|unclear)\b[^.\n;]{0,80}\b(?:dispensed|dispense|came out|medication came out|anything dispensed)\b"
    r"|\b(?:whether|if)\s+(?:any\s+)?medication\s+(?:was\s+)?dispensed\s+(?:is\s+|was\s+)?(?:unknown|unclear|not known)\b",
    re.IGNORECASE,
)

_EXPLICIT_MISSING_SENTENCE_RE = re.compile(
    r"\b(?:missing|unknown|not known|not documented|still need|need to confirm|"
    r"could not confirm|couldn't confirm|unable to determine|confirm|clarify|"
    r"determine whether|could not be evaluated|unable to evaluate)\b",
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



_FIELD_SUPPORT_TERMS: dict[str, tuple[str, ...]] = {
    "record_review_result": (
        "record",
        "worksheet",
        "formula",
        "documentation",
        "discrepancy",
    ),
    "lot_batch_pattern_summary": (
        "lot",
        "batch",
        "trend",
        "similar complaint",
        "similar concern",
    ),
    "inventory_inspection_result": (
        "inventory",
        "inspect",
        "inspected",
        "visual",
    ),
    "customer_context_summary": (
        "customer",
        "owner",
        "dog",
        "cat",
        "pet",
        "vomit",
        "puked",
        "symptom",
        "hospital",
        "vet",
        "veterinarian",
    ),
    "api_reference_review_result": (
        "api",
        "reference",
        "plumb",
        "package insert",
        "drug handbook",
        "usp",
        "manufacturer",
        "clinical guidance",
    ),
    "missing_information": (
        "missing",
        "unknown",
        "not known",
        "still need",
        "need to confirm",
    ),
    "evidence_limitations": (
        "unavailable",
        "not available",
        "not inspected",
        "not checked",
        "not supported",
        "could not",
        "couldn't",
        "unable",
    ),
    "severe_triggers_observed": (
        "death",
        "died",
        "hospital",
        "legal",
        "lawsuit",
        "lawyer",
        "contamination",
        "wrong medication",
        "wrong patient",
        "veterinarian",
        "vet",
        "no severe",
        "no escalation",
    ),
}

_AMBIGUITY_RE = re.compile(
    r"\b(?:maybe|possibly|unclear|unknown|not sure|could not determine|couldn't determine|still investigating|unconfirmed)\b",
    re.IGNORECASE,
)


def extract_review_summary_result(
    reviewer_note: str,
    llm_client: LLMClient,
    *,
    concern_text: str = "",
) -> ReviewSummaryExtractionResult:
    clean_note = reviewer_note.strip()

    if not clean_note:
        raise ValueError("reviewer_note must not be empty")

    summary = extract_review_summary(clean_note, llm_client)
    summary = merge_reported_severe_triggers(
        summary,
        concern_text,
    )
    summary = apply_review_summary_defaults(
        summary,
        concern_text=concern_text,
        reviewer_note=clean_note,
    )
    evidence = build_review_summary_field_evidence(
        reviewer_note=clean_note,
        concern_text=concern_text,
        review_summary=summary,
    )
    unresolved_questions = build_decision_relevant_questions(
        concern_text=concern_text,
        reviewer_note=clean_note,
        review_summary=summary,
    )

    return ReviewSummaryExtractionResult(
        review_summary=summary,
        field_evidence=evidence,
        unresolved_questions=unresolved_questions,
    )


def build_review_summary_field_evidence(
    *,
    reviewer_note: str,
    review_summary: ReviewSummary,
    concern_text: str = "",
) -> list[ReviewSummaryFieldEvidence]:
    summary_data = review_summary.model_dump(mode="json")
    evidence: list[ReviewSummaryFieldEvidence] = []

    for field_name, terms in _FIELD_SUPPORT_TERMS.items():
        supporting_quote = find_supporting_sentence(
            reviewer_note,
            terms,
        )
        if (
            supporting_quote is None
            and field_name == "severe_triggers_observed"
            and concern_text.strip()
        ):
            supporting_quote = find_supporting_sentence(
                concern_text,
                terms,
            )
        status = field_evidence_status(
            field_name=field_name,
            field_value=summary_data.get(field_name),
            supporting_quote=supporting_quote,
        )

        evidence.append(
            ReviewSummaryFieldEvidence(
                field_name=field_name,
                status=status,
                supporting_quote=supporting_quote,
                explanation=field_evidence_explanation(
                    field_name=field_name,
                    status=status,
                ),
            )
        )

    return evidence


def find_supporting_sentence(
    reviewer_note: str,
    terms: Iterable[str],
) -> str | None:
    lowered_terms = tuple(term.lower() for term in terms)

    for sentence in split_sentences(reviewer_note):
        lowered_sentence = sentence.lower()

        if any(term in lowered_sentence for term in lowered_terms):
            return sentence

    return None


def field_evidence_status(
    *,
    field_name: str,
    field_value: Any,
    supporting_quote: str | None,
) -> ExtractionEvidenceStatus:
    if supporting_quote and _AMBIGUITY_RE.search(supporting_quote):
        return ExtractionEvidenceStatus.AMBIGUOUS

    if supporting_quote is None:
        return ExtractionEvidenceStatus.NOT_STATED

    if field_name in _ENUM_FIELDS:
        return ExtractionEvidenceStatus.NORMALIZED

    if field_name in _LIST_FIELDS and not field_value:
        return ExtractionEvidenceStatus.NOT_STATED

    return ExtractionEvidenceStatus.EXPLICIT


def field_evidence_explanation(
    *,
    field_name: str,
    status: ExtractionEvidenceStatus,
) -> str:
    if status == ExtractionEvidenceStatus.NORMALIZED:
        return f"{field_name} was normalized from reviewer wording into the existing enum contract."

    if status == ExtractionEvidenceStatus.EXPLICIT:
        return f"{field_name} is directly supported by the reviewer note."

    if status == ExtractionEvidenceStatus.AMBIGUOUS:
        return f"{field_name} contains uncertain wording and requires reviewer confirmation."

    return f"No direct supporting sentence was found for {field_name}."

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
- If reference review is not mentioned in the reviewer note, use "not_needed".
- If a synthetic reference in the public corpus was consulted, use "synthetic_reference_consulted".
- If USP guidance, manufacturer information, internal clinical guidance, a veterinary drug reference, or a commercial package insert was already reviewed, use "external_reference_consulted".
- If an outside reference still needs to be reviewed, use "external_reference_needed".
- If the requested conclusion or supplier/manufacturer/proprietary information cannot be supported or disclosed, use "not_supported_by_public_corpus" and add an evidence limitation.
- Keep missing_information and evidence_limitations as concise, reviewer-facing strings.
- Do not create a generic checklist of absent fields.
- Add missing_information only when the reviewer note explicitly identifies the information as missing, unknown, or still needed.

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

    data["missing_information"] = infer_grounded_missing_information(
        note,
        data["missing_information"],
    )
    data["evidence_limitations"] = unique_in_order(data["evidence_limitations"])
    data["severe_triggers_observed"] = infer_grounded_severe_triggers(
        note,
        data["severe_triggers_observed"],
    )

    apply_record_review_grounding(note, data)
    apply_lot_batch_grounding(note, data)
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


def merge_reported_severe_triggers(
    summary: ReviewSummary,
    concern_text: str,
) -> ReviewSummary:
    clean_concern = concern_text.strip()
    if not clean_concern:
        return summary

    reported_triggers = infer_grounded_severe_triggers(
        clean_concern,
        [],
    )
    if not reported_triggers:
        return summary

    data = summary.model_dump(mode="json")
    data["severe_triggers_observed"] = sorted(
        set(data["severe_triggers_observed"]) | set(reported_triggers)
    )

    return ReviewSummary.model_validate(data)


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

        if trigger == EscalationTrigger.REPEAT_ISSUE_SAME_LOT_OR_BATCH_WITH_CONDITIONS:
            if re.search(
                r"\b(?:no similar|without similar|no repeat|no trend|trend threshold (?:was )?not met)\b",
                suffix,
                re.IGNORECASE,
            ):
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


def infer_grounded_missing_information(
    reviewer_note: str,
    model_items: Iterable[str],
) -> list[str]:
    grounded: list[str] = []

    if _EXPLICIT_DOSE_MISSING_RE.search(reviewer_note):
        grounded.append("Exact dose administered")

    if _EXPLICIT_DEVICE_DISPENSE_MISSING_RE.search(reviewer_note):
        grounded.append("Whether medication dispensed from the device")

    for sentence in split_sentences(reviewer_note):
        if not _EXPLICIT_MISSING_SENTENCE_RE.search(sentence):
            continue

        normalized = normalize_explicit_missing_sentence(sentence)
        if normalized is not None:
            grounded.append(normalized)

    _ = model_items
    return unique_in_order(grounded)


def normalize_explicit_missing_sentence(sentence: str) -> str | None:
    lowered = sentence.lower()
    cleaned = re.sub(
        r"^unresolved investigation items:\s*",
        "",
        sentence.strip(),
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"^(?:confirm|clarify|determine whether)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip(" .")

    if "storage" in lowered or "temperature" in lowered:
        return "Storage and temperature conditions"
    if "shaking" in lowered or "resuspension" in lowered:
        return "Shaking and resuspension technique"
    if "syringe" in lowered or "measurement technique" in lowered:
        return "Syringe selection and measurement technique"
    if "other medications" in lowered or "concurrent therapy" in lowered:
        return "Other medications and concurrent therapy"
    if "dose appropriateness" in lowered and any(
        phrase in lowered
        for phrase in (
            "could not be evaluated",
            "unable to evaluate",
            "could not evaluate",
        )
    ):
        return "Dose appropriateness from the available directions"

    if "dose" in lowered:
        return "Exact dose administered"
    if "event timeline" in lowered or "timeline" in lowered:
        return "Event timeline"
    if "reported symptoms" in lowered or (
        "symptom" in lowered and "severity" in lowered
    ):
        return "Reported symptoms and severity"
    if "transdermal" in lowered and any(
        term in lowered for term in ("rotation", "cleaning", "site")
    ):
        return "Transdermal application-site rotation and cleaning"
    if "leakage" in lowered or "physical damage" in lowered:
        return "Whether leakage or physical damage was observed"
    if "exposure duration" in lowered or "number of doses" in lowered:
        return "Exposure duration and number of doses administered"
    if "device behavior" in lowered or "usable medication" in lowered or any(
        term in lowered for term in ("dispense", "dispensed", "came out")
    ):
        return "Whether medication dispensed from the device"
    if "veterinarian" in lowered or re.search(r"\bvet\b", lowered):
        return "Veterinarian involvement and recommendations"
    if "lot" in lowered or "batch" in lowered:
        return "Lot or batch trend information"
    if "shortage" in lowered:
        return "Whether there was a confirmed shortage"
    return cleaned or None


def apply_record_review_grounding(note: str, data: dict[str, Any]) -> None:
    if _RECORD_NOT_APPLICABLE_RE.search(note):
        data["record_review_result"] = RecordReviewResult.NOT_APPLICABLE.value
        return

    if _RECORD_INCOMPLETE_RE.search(note):
        data["record_review_result"] = RecordReviewResult.DOCUMENTATION_INCOMPLETE.value
        return

    if _RECORD_DISCREPANCY_RE.search(note):
        if not re.search(
            r"\b(?:ruled out|no wrong medication|no wrong patient|correct medication and patient|correct patient and medication)\b",
            note,
            re.IGNORECASE,
        ):
            data["record_review_result"] = (
                RecordReviewResult.DOCUMENTATION_DISCREPANCY_FOUND.value
            )
            return

    if _RECORD_NO_DISCREPANCY_RE.search(note):
        data["record_review_result"] = RecordReviewResult.NO_DISCREPANCY_FOUND.value


def apply_lot_batch_grounding(note: str, data: dict[str, Any]) -> None:
    if _LOT_NOT_APPLICABLE_RE.search(note):
        data["lot_batch_pattern_summary"] = LotBatchPatternSummary.NOT_APPLICABLE.value
        return

    if _LOT_TREND_THRESHOLD_RE.search(note):
        data["lot_batch_pattern_summary"] = LotBatchPatternSummary.TREND_THRESHOLD_MET.value
        return

    if _LOT_NO_SIMILAR_RE.search(note):
        data["lot_batch_pattern_summary"] = (
            LotBatchPatternSummary.NO_SIMILAR_BATCH_CONCERNS_FOUND.value
        )
        return

    if _LOT_SAME_BATCH_FOUND_RE.search(note):
        data["lot_batch_pattern_summary"] = (
            LotBatchPatternSummary.SIMILAR_CONCERN_SAME_BATCH_FOUND.value
        )
        return

    if _LOT_SAME_PRODUCT_FOUND_RE.search(note):
        data["lot_batch_pattern_summary"] = (
            LotBatchPatternSummary.SIMILAR_CONCERN_SAME_MEDICATION_DOSAGE_FORM_FOUND.value
        )
        return

    if _LOT_UNAVAILABLE_RE.search(note):
        data["lot_batch_pattern_summary"] = LotBatchPatternSummary.UNAVAILABLE.value


def apply_inventory_grounding(note: str, data: dict[str, Any]) -> None:
    if _INVENTORY_NOT_APPLICABLE_RE.search(note):
        data["inventory_inspection_result"] = InventoryInspectionResult.NOT_APPLICABLE.value
        return

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
        return

    if _INVENTORY_NO_VISUAL_RE.search(note):
        data["inventory_inspection_result"] = InventoryInspectionResult.NO_VISUAL_CONCERN_FOUND.value
        return

    if _INVENTORY_VISUAL_CONCERN_RE.search(note):
        data["inventory_inspection_result"] = InventoryInspectionResult.VISUAL_CONCERN_FOUND.value


def apply_api_reference_grounding(note: str, data: dict[str, Any]) -> None:
    if _NON_DISCLOSURE_RE.search(note) or _EXTERNAL_UNSUPPORTED_RE.search(note):
        data["api_reference_review_result"] = (
            ApiReferenceReviewResult.NOT_SUPPORTED_BY_PUBLIC_CORPUS.value
        )
        add_unique(
            data["evidence_limitations"],
            "The requested external, supplier, manufacturer, or proprietary information is not supported for disclosure by the public corpus.",
        )
        return

    if _EXTERNAL_CONSULTED_RE.search(note):
        data["api_reference_review_result"] = (
            ApiReferenceReviewResult.EXTERNAL_REFERENCE_CONSULTED.value
        )
        return

    if _SYNTHETIC_REFERENCE_RE.search(note):
        data["api_reference_review_result"] = (
            ApiReferenceReviewResult.SYNTHETIC_REFERENCE_CONSULTED.value
        )
        return

    if _API_NOT_NEEDED_RE.search(note):
        data["api_reference_review_result"] = (
            ApiReferenceReviewResult.NOT_NEEDED.value
        )
        return

    if _EXTERNAL_NEEDED_RE.search(note):
        data["api_reference_review_result"] = (
            ApiReferenceReviewResult.EXTERNAL_REFERENCE_NEEDED.value
        )

    data["api_reference_review_result"] = (
        ApiReferenceReviewResult.NOT_NEEDED.value
    )

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
