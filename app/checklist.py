from __future__ import annotations

from pathlib import Path

from app.checklist_models import EvidenceCitation, ChecklistItem, IntakeChecklist
from app.retrieval import DEFAULT_CHUNKS_PATH, SearchResult, retrieve
from app.schemas import ConcernType, EscalationTrigger, RiskLane, SourceType


VOMITING_TERMS = {"vomit", "vomited", "vomiting", "threw up", "throwing up"}
FLAVOR_TERMS = {"flavor", "flavored", "chicken", "beef", "tuna", "palatability", "refuse", "refused"}
TRANSDERMAL_TERMS = {"transdermal", "pen", "click", "clicks", "leak", "leaking", "air bubbles"}
BUD_TERMS = {"bud", "beyond use", "beyond-use", "expiration", "expired"}
WRONG_MEDICATION_TERMS = {"wrong medication", "wrong patient", "wrong med", "dispensing error"}


def build_intake_checklist(
    concern_text: str,
    *,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    top_k: int = 5,
) -> IntakeChecklist:
    clean_text = concern_text.strip()

    if not clean_text:
        raise ValueError("concern_text must not be empty")

    retrieved_chunks = retrieve(
        query=clean_text,
        chunks_path=chunks_path,
        top_k=top_k,
        source_type=SourceType.SOP.value,
    )

    evidence = build_evidence_citations(retrieved_chunks)

    likely_concern_type = infer_likely_concern_type(clean_text)
    likely_risk_lane = infer_likely_risk_lane(clean_text)

    return IntakeChecklist(
        concern_text=clean_text,
        likely_concern_type=likely_concern_type,
        likely_risk_lane=likely_risk_lane,
        review_checks=build_review_checks(clean_text, evidence),
        missing_information=build_missing_information(clean_text),
        escalation_triggers_to_rule_out=build_escalation_triggers_to_rule_out(clean_text),
        evidence=evidence,
        limitations=[
            "This synthetic assistant does not access real compounding records, inventory, customer history, or external drug references.",
            "Phase 1 output is a review checklist, not a final clinical or legal conclusion.",
            "Causality should not be inferred from the intake narrative alone.",
        ],
    )


def build_evidence_citations(search_results: list[SearchResult]) -> list[EvidenceCitation]:
    citations: list[EvidenceCitation] = []

    for result in search_results:
        chunk = result["chunk"]
        citations.append(
            EvidenceCitation(
                chunk_id=chunk["chunk_id"],
                source_id=chunk["source_id"],
                source_title=chunk["source_title"],
                source_type=chunk["source_type"],
                section_heading=chunk["section_heading"],
                score=float(result["score"]),
                matched_terms=result["matched_terms"],
                supporting_text=chunk["text"],
            )
        )

    return citations


def infer_likely_concern_type(concern_text: str) -> ConcernType | None:
    normalized = concern_text.lower()

    if contains_any(normalized, WRONG_MEDICATION_TERMS):
        return ConcernType.WRONG_PATIENT_OR_WRONG_MEDICATION

    if contains_any(normalized, VOMITING_TERMS):
        if contains_any(normalized, FLAVOR_TERMS):
            return ConcernType.FLAVOR_RELATED_VOMITING
        return ConcernType.POSSIBLE_ADVERSE_DRUG_EVENT

    if contains_any(normalized, TRANSDERMAL_TERMS):
        return ConcernType.SYRINGE_OR_DEVICE_ISSUE

    if contains_any(normalized, BUD_TERMS):
        return ConcernType.BUD_QUESTION

    if contains_any(normalized, FLAVOR_TERMS):
        return ConcernType.PET_REFUSED_FLAVOR

    return None


def infer_likely_risk_lane(concern_text: str) -> RiskLane | None:
    normalized = concern_text.lower()

    severe_terms = {
        "died", "death", "hospitalized", "hospitalization", "legal", "lawsuit", "lawyer",
        "vet said", "veterinarian said", "contamination", "contaminated", "wrong medication", "wrong patient",
    }

    if contains_any(normalized, severe_terms):
        return RiskLane.LIFE_THREATENING_OR_LEGAL

    if contains_any(normalized, VOMITING_TERMS):
        return RiskLane.UNEXPECTED_NON_LIFE_THREATENING

    if contains_any(normalized, FLAVOR_TERMS | TRANSDERMAL_TERMS | BUD_TERMS):
        return RiskLane.EXPECTED_SELF_LIMITING

    return None


def build_review_checks(concern_text: str, evidence: list[EvidenceCitation]) -> list[ChecklistItem]:
    normalized = concern_text.lower()
    checks = [
        ChecklistItem(
            check_name="Record review",
            required=True,
            rationale="Verify the synthetic compounding or dispensing record fields relevant to the concern.",
            evidence=evidence[:2],
        ),
        ChecklistItem(
            check_name="Lot or batch context review",
            required=True,
            rationale="Look for similar concerns tied to the same lot, batch, medication, dosage form, or concern type when those fields are available.",
            evidence=evidence[:2],
        ),
        ChecklistItem(
            check_name="Inventory inspection if available",
            required=True,
            rationale="Inspect available inventory when the concern could involve visible product quality, device, equipment, or packaging issues.",
            evidence=evidence[:2],
        ),
        ChecklistItem(
            check_name="Trend scan",
            required=True,
            rationale="Check for repeated similar concerns when enough synthetic fields exist to support trend review.",
            evidence=evidence[:2],
        ),
    ]

    if contains_any(normalized, VOMITING_TERMS):
        checks.append(
            ChecklistItem(
                check_name="Customer clinical context follow-up",
                required=True,
                rationale="Vomiting after administration requires timing, dose, symptom course, veterinarian contact, and severity context before final routing.",
                evidence=evidence[:3],
            )
        )

    if contains_any(normalized, TRANSDERMAL_TERMS):
        checks.append(
            ChecklistItem(
                check_name="Device administration context",
                required=True,
                rationale="Transdermal device concerns require details on clicks, leaking, air bubbles, and whether medication could be administered.",
                evidence=evidence[:3],
            )
        )

    if contains_any(normalized, BUD_TERMS):
        checks.append(
            ChecklistItem(
                check_name="BUD field review",
                required=True,
                rationale="BUD questions require preparation date, assigned BUD, review or dispense date, and relevant storage context.",
                evidence=evidence[:3],
            )
        )

    return checks


def build_missing_information(concern_text: str) -> list[str]:
    normalized = concern_text.lower()
    missing = [
        "Medication or product placeholder",
        "Species",
        "Dosage form",
        "Lot or batch information if available",
        "Whether any severe escalation trigger is present",
    ]

    if contains_any(normalized, VOMITING_TERMS):
        missing.extend(
            [
                "Dose administered",
                "Timing of vomiting relative to administration",
                "Whether symptoms resolved",
                "Whether veterinarian was contacted",
                "Whether the pet was hospitalized",
            ]
        )

    if contains_any(normalized, TRANSDERMAL_TERMS):
        missing.extend(
            [
                "Whether the device leaked from the top or bottom",
                "Whether air bubbles were observed",
                "Whether the device dispensed after expected clicks",
                "Whether the customer has enough usable medication remaining",
            ]
        )

    if contains_any(normalized, BUD_TERMS):
        missing.extend(
            [
                "Preparation date",
                "Assigned beyond-use date",
                "Dispense or review date",
                "Storage conditions if relevant",
            ]
        )

    return unique_in_order(missing)


def build_escalation_triggers_to_rule_out(concern_text: str) -> list[EscalationTrigger]:
    normalized = concern_text.lower()

    triggers = [
        EscalationTrigger.PET_DEATH,
        EscalationTrigger.PET_HOSPITALIZATION,
        EscalationTrigger.THREATENED_LEGAL_ACTION,
        EscalationTrigger.VETERINARIAN_ALLEGES_HARM_FROM_COMPOUND,
        EscalationTrigger.POSSIBLE_CONTAMINATION,
        EscalationTrigger.WRONG_PATIENT_OR_WRONG_MEDICATION,
    ]

    if "lot" in normalized or "batch" in normalized:
        triggers.append(EscalationTrigger.REPEAT_ISSUE_SAME_LOT_OR_BATCH_WITH_CONDITIONS)

    return triggers


def contains_any(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)


def unique_in_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []

    for value in values:
        if value in seen:
            continue

        seen.add(value)
        output.append(value)

    return output
