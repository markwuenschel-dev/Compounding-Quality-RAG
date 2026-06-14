from __future__ import annotations

import re
from collections.abc import Iterable

from app.schemas import ReviewSummary, UnresolvedReviewQuestion


_VOMITING_TERMS = (
    "vomit",
    "vomited",
    "vomiting",
    "puked",
    "threw up",
)

_DEVICE_TERMS = (
    "transdermal",
    "pen",
    "click",
    "clicks",
    "leak",
    "leaking",
    "air bubble",
    "air bubbles",
)

_BUD_TERMS = (
    "bud",
    "beyond-use",
    "beyond use",
    "expired",
    "expiration",
)

_DOSE_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:ml|milliliters?|mg|milligrams?|mcg|micrograms?|units?|tablets?|capsules?|clicks?)\b",
    re.IGNORECASE,
)

_TIMING_RE = re.compile(
    r"\b(?:about\s+)?\d+\s*(?:minutes?|mins?|hours?|hrs?)\b|\b(?:immediately|right after|shortly after|later)\b",
    re.IGNORECASE,
)

_RESOLUTION_RE = re.compile(
    r"\b(?:resolved|recovered|fine now|okay now|ok now|doing well|still vomiting|continued vomiting|ongoing symptoms?)\b",
    re.IGNORECASE,
)

_VET_CONTACT_RE = re.compile(
    r"\b(?:vet|veterinarian|emergency clinic|animal hospital)\b",
    re.IGNORECASE,
)

_HOSPITALIZATION_RE = re.compile(
    r"\b(?:hospitalized|hospitalised|hospitalization|hospitalisation|er visit|emergency hospital|admitted|not hospitalized|no hospitalization|no er visit)\b",
    re.IGNORECASE,
)

_WRONG_MEDICATION_RE = re.compile(
    r"\b(?:wrong medication|wrong med|wrong patient|dispensing error)\b",
    re.IGNORECASE,
)

_CONTAMINATION_RE = re.compile(
    r"\b(?:contamination|contaminated|foreign material|mold|particulate)\b",
    re.IGNORECASE,
)

_RULED_OUT_RE = re.compile(
    r"\b(?:ruled out|not present|not observed|not reported|no evidence of|confirmed absent)\b",
    re.IGNORECASE,
)


_CORRECT_MEDICATION_PATIENT_RE = re.compile(
    r"\b(?:confirmed|verified|documented)\s+(?:the\s+)?correct\s+(?:medication\s+and\s+patient|patient\s+and\s+medication)\b"
    r"|\b(?:medication|patient)\s+(?:was\s+)?confirmed\s+correct\b",
    re.IGNORECASE,
)

_DEVICE_DISPENSE_UNRESOLVED_RE = re.compile(
    r"\b(?:could not confirm|couldn't confirm|unable to confirm|not sure|unknown|unclear)\b[^.\n;]{0,80}\b(?:dispensed|dispense|came out|anything dispensed)\b",
    re.IGNORECASE,
)

_DEVICE_DISPENSE_RE = re.compile(
    r"\b(?:dispensed|did not dispense|would not dispense|medication came out|no medication came out|usable medication remaining)\b",
    re.IGNORECASE,
)

_DATE_RE = re.compile(
    r"\b(?:\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}|preparation date|dispense date|assigned bud|beyond-use date)\b",
    re.IGNORECASE,
)


def build_decision_relevant_questions(
    *,
    concern_text: str,
    reviewer_note: str,
    review_summary: ReviewSummary,
) -> list[UnresolvedReviewQuestion]:
    concern = concern_text.strip().lower()
    note = reviewer_note.strip()
    combined = f"{concern_text}\n{reviewer_note}".strip()
    questions: list[UnresolvedReviewQuestion] = []

    if contains_any(concern, _VOMITING_TERMS):
        if not _HOSPITALIZATION_RE.search(combined):
            questions.append(
                question(
                    field_name="hospitalization_status",
                    question_text="Was the patient hospitalized or evaluated at an emergency hospital?",
                    reason="Hospitalization status can change the risk lane and escalation path.",
                    decision_impact=["risk_lane", "escalation", "handling_path"],
                )
            )

        if not _RESOLUTION_RE.search(combined):
            questions.append(
                question(
                    field_name="symptom_resolution",
                    question_text="Did the reported symptoms resolve, continue, or worsen?",
                    reason="Symptom course affects severity context and follow-up urgency.",
                    decision_impact=["risk_lane", "handling_path"],
                )
            )

        if not _VET_CONTACT_RE.search(combined):
            questions.append(
                question(
                    field_name="veterinarian_contact",
                    question_text="Was a veterinarian contacted, and did the veterinarian allege harm from the compound?",
                    reason="Veterinarian involvement can change escalation requirements.",
                    decision_impact=["escalation", "handling_path"],
                )
            )

        if not _DOSE_RE.search(combined):
            questions.append(
                question(
                    field_name="dose_administered",
                    question_text="What dose was administered?",
                    reason="Dose context is relevant to interpreting the reported event.",
                    decision_impact=["review_scope", "handling_path"],
                )
            )

        if not _TIMING_RE.search(combined):
            questions.append(
                question(
                    field_name="event_timing",
                    question_text="How long after administration did the event occur?",
                    reason="Timing helps distinguish the reported sequence without asserting causality.",
                    decision_impact=["review_scope", "handling_path"],
                )
            )

    wrong_medication_ruled_out = (
        _WRONG_MEDICATION_RE.search(note) and _RULED_OUT_RE.search(note)
    ) or _CORRECT_MEDICATION_PATIENT_RE.search(note)

    if _WRONG_MEDICATION_RE.search(concern) and not wrong_medication_ruled_out:
        if not review_summary.severe_triggers_observed:
            questions.append(
                question(
                    field_name="wrong_medication_status",
                    question_text="Was a wrong-patient or wrong-medication issue confirmed, ruled out, or still possible?",
                    reason="A confirmed or still-possible dispensing error requires conservative escalation.",
                    decision_impact=["risk_lane", "escalation", "handling_path"],
                )
            )

    if _CONTAMINATION_RE.search(concern) and not (
        _CONTAMINATION_RE.search(note) and _RULED_OUT_RE.search(note)
    ):
        if not review_summary.severe_triggers_observed:
            questions.append(
                question(
                    field_name="contamination_status",
                    question_text="Was possible contamination confirmed, ruled out, or still unresolved?",
                    reason="Possible contamination can require escalation before routine resolution.",
                    decision_impact=["risk_lane", "escalation", "handling_path"],
                )
            )

    device_dispense_unresolved = _DEVICE_DISPENSE_UNRESOLVED_RE.search(combined)
    device_dispense_documented = _DEVICE_DISPENSE_RE.search(combined)

    if contains_any(concern, _DEVICE_TERMS) and (
        device_dispense_unresolved or not device_dispense_documented
    ):
        questions.append(
            question(
                field_name="device_dispense_status",
                question_text="Did the device dispense medication, and is usable medication still available?",
                reason="Device function affects the quality review and possible replacement path.",
                decision_impact=["review_scope", "resolution_options"],
            )
        )

    if contains_any(concern, _BUD_TERMS) and not _DATE_RE.search(combined):
        questions.append(
            question(
                field_name="bud_date_context",
                question_text="What were the preparation date, assigned BUD, and dispense or review date?",
                reason="BUD interpretation depends on record-specific dates.",
                decision_impact=["review_scope", "handling_path"],
            )
        )

    if (
        "lot" in concern or "batch" in concern
    ) and review_summary.lot_batch_pattern_summary.value == "unavailable":
        questions.append(
            question(
                field_name="lot_batch_context",
                question_text="Is lot or batch trend information available from the reviewer?",
                reason="A same-lot pattern can change escalation and investigation scope.",
                decision_impact=["escalation", "review_scope"],
            )
        )

    return unique_questions(questions)


def question(
    *,
    field_name: str,
    question_text: str,
    reason: str,
    decision_impact: list[str],
) -> UnresolvedReviewQuestion:
    return UnresolvedReviewQuestion(
        field_name=field_name,
        question=question_text,
        reason=reason,
        decision_impact=decision_impact,
    )


def contains_any(text: str, terms: Iterable[str]) -> bool:
    return any(term in text for term in terms)


def unique_questions(
    questions: list[UnresolvedReviewQuestion],
) -> list[UnresolvedReviewQuestion]:
    seen: set[str] = set()
    output: list[UnresolvedReviewQuestion] = []

    for item in questions:
        if item.field_name in seen:
            continue

        seen.add(item.field_name)
        output.append(item)

    return output
