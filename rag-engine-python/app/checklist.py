from __future__ import annotations

import re
from pathlib import Path

from app.checklist_models import EvidenceCitation, ChecklistItem, IntakeChecklist
from app.extract_intake_understanding import IntakeUnderstanding
from app.retrieval import DEFAULT_CHUNKS_PATH, SearchResult, retrieve
from app.schemas import ConcernType, EscalationTrigger, RiskLane, SourceType


VOMITING_TERMS = {"vomit", "vomited", "vomiting", "threw up", "throwing up"}
FLAVOR_TERMS = {
    "flavor",
    "flavored",
    "chicken",
    "beef",
    "tuna",
    "palatability",
    "refuse",
    "refused",
}
TRANSDERMAL_TERMS = {
    "transdermal",
    "pen",
    "click",
    "clicks",
    "leak",
    "leaking",
    "air bubbles",
}
BUD_TERMS = {"bud", "beyond use", "beyond-use", "expiration", "expired"}
WRONG_MEDICATION_TERMS = {
    "wrong medication",
    "wrong patient",
    "wrong med",
    "dispensing error",
}
ORAL_LIQUID_TERMS = {
    "oral liquid",
    "compounded liquid",
    "liquid",
    "suspension",
    "solution",
}
FLAVOR_REJECTION_TERMS = {
    "foamed",
    "foaming",
    "foamed at the mouth",
    "drooled",
    "drooling",
    "salivating",
    "hypersalivation",
    "spit out",
    "spat out",
    "refused",
    "wouldn't take",
}

SPECIES_TERMS = {
    "dog",
    "canine",
    "cat",
    "feline",
    "horse",
    "equine",
}
DOSAGE_FORM_TERMS = {
    "oral liquid",
    "oral suspension",
    "oral solution",
    "suspension",
    "solution",
    "capsule",
    "tablet",
    "transdermal",
    "chewable",
    "powder",
    "ophthalmic",
    "oral paste",
    "topical",
    "cream",
    "gel",
    "ointment",
}

DOSE_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:ml|milliliters?|mg|milligrams?|mcg|micrograms?|units?|tablets?|capsules?|clicks?)\b",
    re.IGNORECASE,
)
TIMING_RE = re.compile(
    r"\b(?:about\s+)?\d+\s*(?:minutes?|mins?|hours?|hrs?)\b|\b(?:immediately|right after|shortly after|later)\b",
    re.IGNORECASE,
)
RESOLUTION_RE = re.compile(
    r"\b(?:seems? okay|seems? ok|fine now|okay now|ok now|recovered|resolved|doing well|back to normal|still vomiting|continued vomiting|ongoing symptoms?)\b",
    re.IGNORECASE,
)
VETERINARIAN_CONTEXT_RE = re.compile(
    r"\b(?:vet|veterinarian|animal hospital|emergency clinic)\b",
    re.IGNORECASE,
)
HOSPITALIZATION_CONTEXT_RE = re.compile(
    r"\b(?:hospitalized|hospitalised|hospitalization|hospitalisation|admitted|no er visit|er visit|emergency hospital|not hospitalized|not hospitalised)\b",
    re.IGNORECASE,
)
LOT_BATCH_IDENTIFIER_RE = re.compile(
    r"\b(?:lot|batch)\s*(?:number|no\.?|#)?\s*[a-z0-9-]{3,}\b",
    re.IGNORECASE,
)

CONCERN_RETRIEVAL_TERMS: dict[ConcernType, tuple[str, ...]] = {
    ConcernType.FLAVOR_RELATED_VOMITING: (
        "suspected adverse event",
        "vomiting after administration",
        "customer clinical context",
        "hospitalization",
        "veterinarian",
        "escalation",
    ),
    ConcernType.POSSIBLE_ADVERSE_DRUG_EVENT: (
        "suspected adverse event",
        "customer clinical context",
        "hospitalization",
        "veterinarian",
        "escalation",
    ),
    ConcernType.SYRINGE_OR_DEVICE_ISSUE: (
        "device administration",
        "dispense",
        "clicks",
        "leaking",
        "air bubbles",
    ),
    ConcernType.BUD_QUESTION: (
        "beyond use date",
        "preparation date",
        "dispense date",
        "storage conditions",
    ),
    ConcernType.WRONG_PATIENT_OR_WRONG_MEDICATION: (
        "wrong patient",
        "wrong medication",
        "dispensing error",
        "escalation",
    ),
}

CONCERN_RERANK_TERMS: dict[ConcernType, tuple[str, ...]] = {
    ConcernType.FLAVOR_RELATED_VOMITING: (
        "vomit",
        "adverse event",
        "clinical context",
        "hospital",
        "veterinarian",
    ),
    ConcernType.POSSIBLE_ADVERSE_DRUG_EVENT: (
        "adverse event",
        "clinical context",
        "hospital",
        "veterinarian",
    ),
    ConcernType.SYRINGE_OR_DEVICE_ISSUE: (
        "device",
        "transdermal",
        "click",
        "leak",
        "dispense",
    ),
    ConcernType.BUD_QUESTION: (
        "beyond-use",
        "beyond use",
        "bud",
        "preparation date",
        "storage",
    ),
    ConcernType.WRONG_PATIENT_OR_WRONG_MEDICATION: (
        "wrong patient",
        "wrong medication",
        "dispensing error",
    ),
}


def build_intake_checklist(
    concern_text: str,
    *,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    top_k: int = 5,
    intake_understanding: IntakeUnderstanding | None = None,
) -> IntakeChecklist:
    clean_text = concern_text.strip()

    if not clean_text:
        raise ValueError("concern_text must not be empty")

    likely_concern_type = infer_likely_concern_type(clean_text)
    likely_risk_lane = infer_likely_risk_lane(clean_text)
    retrieval_query = build_retrieval_query(
        clean_text,
        likely_concern_type,
    )
    candidate_count = max(top_k * 3, top_k)
    retrieved_chunks = retrieve(
        query=retrieval_query,
        chunks_path=chunks_path,
        top_k=candidate_count,
        source_type=SourceType.SOP.value,
    )
    reranked_chunks = rerank_for_concern_type(
        retrieved_chunks,
        likely_concern_type,
    )[:top_k]
    evidence = build_evidence_citations(reranked_chunks)

    return IntakeChecklist(
        concern_text=clean_text,
        likely_concern_type=likely_concern_type,
        likely_risk_lane=likely_risk_lane,
        review_checks=build_review_checks(clean_text, evidence),
        missing_information=build_missing_information(
            clean_text,
            intake_understanding=intake_understanding,
        ),
        escalation_triggers_to_rule_out=(
            build_escalation_triggers_to_rule_out(clean_text)
        ),
        evidence=evidence,
        limitations=[
            "This synthetic assistant does not access real compounding records, inventory, customer history, or external drug references.",
            "Phase 1 output is a review checklist, not a final clinical or legal conclusion.",
            "Causality should not be inferred from the intake narrative alone.",
        ],
    )


def build_retrieval_query(
    concern_text: str,
    concern_type: ConcernType | None,
) -> str:
    if concern_type is None:
        return concern_text

    expansion = CONCERN_RETRIEVAL_TERMS.get(concern_type, ())

    if not expansion:
        return concern_text

    return " ".join([concern_text, *expansion])


def rerank_for_concern_type(
    search_results: list[SearchResult],
    concern_type: ConcernType | None,
) -> list[SearchResult]:
    if concern_type is None:
        return search_results

    preferred_terms = CONCERN_RERANK_TERMS.get(concern_type, ())

    if not preferred_terms:
        return search_results

    reranked: list[SearchResult] = []

    for result in search_results:
        chunk = result["chunk"]
        searchable_text = " ".join(
            [
                chunk["source_title"],
                chunk["section_heading"],
                chunk["text"],
            ]
        ).lower()
        bonus = sum(
            3.0
            for term in preferred_terms
            if term in searchable_text
        )
        reranked.append(
            {
                "chunk": chunk,
                "score": result["score"] + bonus,
                "matched_terms": result["matched_terms"],
            }
        )

    return sorted(
        reranked,
        key=lambda result: (
            -result["score"],
            result["chunk"]["chunk_id"],
        ),
    )


def build_evidence_citations(
    search_results: list[SearchResult],
) -> list[EvidenceCitation]:
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


def infer_likely_concern_type(
    concern_text: str,
) -> ConcernType | None:
    normalized = concern_text.lower()

    if contains_any(normalized, WRONG_MEDICATION_TERMS):
        return ConcernType.WRONG_PATIENT_OR_WRONG_MEDICATION

    if contains_any(normalized, VOMITING_TERMS):
        if contains_any(normalized, FLAVOR_TERMS):
            return ConcernType.FLAVOR_RELATED_VOMITING
        return ConcernType.POSSIBLE_ADVERSE_DRUG_EVENT

    if contains_any(normalized, FLAVOR_REJECTION_TERMS):
        return ConcernType.PET_REFUSED_FLAVOR

    if contains_any(normalized, TRANSDERMAL_TERMS):
        return ConcernType.SYRINGE_OR_DEVICE_ISSUE

    if contains_any(normalized, BUD_TERMS):
        return ConcernType.BUD_QUESTION

    if contains_any(normalized, FLAVOR_TERMS):
        return ConcernType.PET_REFUSED_FLAVOR

    return None


def infer_likely_risk_lane(
    concern_text: str,
) -> RiskLane | None:
    normalized = concern_text.lower()
    severe_terms = {
        "died",
        "death",
        "hospitalized",
        "hospitalization",
        "legal",
        "lawsuit",
        "lawyer",
        "vet said",
        "veterinarian said",
        "contamination",
        "contaminated",
        "wrong medication",
        "wrong patient",
        "seizure",
        "seizures",
        "collapsed",
        "collapse",
        "trouble breathing",
        "difficulty breathing",
        "could not breathe",
        "unresponsive",
    }

    if contains_any(normalized, severe_terms):
        return RiskLane.LIFE_THREATENING_OR_LEGAL

    if contains_any(normalized, VOMITING_TERMS):
        return RiskLane.UNEXPECTED_NON_LIFE_THREATENING

    if contains_any(
        normalized,
        FLAVOR_TERMS
        | FLAVOR_REJECTION_TERMS
        | TRANSDERMAL_TERMS
        | ORAL_LIQUID_TERMS
        | BUD_TERMS,
    ):
        return RiskLane.EXPECTED_SELF_LIMITING

    return None


def build_review_checks(
    concern_text: str,
    evidence: list[EvidenceCitation],
) -> list[ChecklistItem]:
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


def build_missing_information(
    concern_text: str,
    intake_understanding: IntakeUnderstanding | None = None,
) -> list[str]:
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

    if contains_any(normalized, FLAVOR_REJECTION_TERMS):
        missing.extend(
            [
                "Flavor or base if available",
                "Whether the pet swallowed the dose or spit it out",
                "Whether this was the first dose or a repeat dose",
                "Whether the pet previously tolerated this medication or flavor",
                "Whether symptoms resolved without further issue",
            ]
        )

    return filter_known_information(
        missing,
        concern_text=concern_text,
        intake_understanding=intake_understanding,
    )


def filter_known_information(
    missing: list[str],
    *,
    concern_text: str,
    intake_understanding: IntakeUnderstanding | None,
) -> list[str]:
    known_text = concern_text.lower()
    species_known = contains_any(known_text, SPECIES_TERMS)
    dosage_form_known = contains_any(known_text, DOSAGE_FORM_TERMS)
    flavor_known = contains_any(known_text, FLAVOR_TERMS)

    if intake_understanding is not None:
        product_context = intake_understanding.product_context
        facts_present = " ".join(
            intake_understanding.facts_present
        ).lower()
        customer_context = (
            intake_understanding.extracted_customer_context or ""
        ).lower()
        known_text = " ".join(
            [known_text, facts_present, customer_context]
        )
        species_known = (
            species_known
            or product_context.species.value != "unknown"
        )
        dosage_form_known = (
            dosage_form_known
            or product_context.dosage_form.value != "unknown"
        )
        flavor_known = (
            flavor_known
            or product_context.flavor_or_attribute is not None
        )

    filtered: list[str] = []

    for item in missing:
        item_lower = item.lower()

        if item_lower == "species" and species_known:
            continue

        if item_lower == "dosage form" and dosage_form_known:
            continue

        if "flavor" in item_lower and flavor_known:
            continue

        if "lot or batch information" in item_lower and LOT_BATCH_IDENTIFIER_RE.search(known_text):
            continue

        if item_lower == "dose administered" and DOSE_RE.search(known_text):
            continue

        if "timing of vomiting" in item_lower and TIMING_RE.search(known_text):
            continue

        if "whether symptoms resolved" in item_lower and RESOLUTION_RE.search(known_text):
            continue

        if "veterinarian was contacted" in item_lower and VETERINARIAN_CONTEXT_RE.search(known_text):
            continue

        if "pet was hospitalized" in item_lower and HOSPITALIZATION_CONTEXT_RE.search(known_text):
            continue

        if "air bubbles" in item_lower and "air bubble" in known_text:
            continue

        if "swallowed the dose or spit it out" in item_lower and (
            "swallowed" in known_text
            or "spit it out" in known_text
            or "spat it out" in known_text
        ):
            continue

        filtered.append(item)

    return unique_in_order(filtered)


def build_escalation_triggers_to_rule_out(
    concern_text: str,
) -> list[EscalationTrigger]:
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
        triggers.append(
            EscalationTrigger.REPEAT_ISSUE_SAME_LOT_OR_BATCH_WITH_CONDITIONS
        )

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
