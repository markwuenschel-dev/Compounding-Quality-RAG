from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from app.schemas import StrictBaseModel


class RefusalReason(StrEnum):
    EXTERNAL_DRUG_REFERENCE = "external_drug_reference"
    INTERNAL_RECORD_ACCESS = "internal_record_access"
    CLINICAL_OR_LEGAL_CONCLUSION = "clinical_or_legal_conclusion"


class RefusalResult(StrictBaseModel):
    refused: bool
    reason: RefusalReason | None = None
    message: str | None = None
    matched_terms: list[str] = Field(default_factory=list)


EXTERNAL_REFERENCE_TERMS = {
    "plumb",
    "plumb's",
    "plumbs",
    "drug handbook",
    "package insert",
    "external reference",
    "published adverse effects",
    "exact adverse effects",
    "contraindications",
    "drug interactions",
    "species-specific toxicity",
    "toxicity",
    "dose range",
    "therapeutic dose",
}

INTERNAL_RECORD_ACCESS_TERMS = {
    "real compounding record",
    "actual compounding record",
    "order page",
    "customer history",
    "customer record",
    "patient record",
    "look up the order",
    "check the real record",
    "inventory record",
    "real inventory",
}

CLINICAL_OR_LEGAL_CONCLUSION_TERMS = {
    "is this medication safe",
    "did this medication cause",
    "is chewy liable",
    "legal advice",
    "clinical diagnosis",
    "diagnose",
    "caused the death",
}


def evaluate_refusal(concern_text: str) -> RefusalResult:
    clean_text = concern_text.strip()

    if not clean_text:
        raise ValueError("concern_text must not be empty")

    normalized = clean_text.lower()

    external_matches = matched_terms(normalized, EXTERNAL_REFERENCE_TERMS)
    if external_matches:
        return build_refusal_result(
            reason=RefusalReason.EXTERNAL_DRUG_REFERENCE,
            matched=external_matches,
        )

    internal_matches = matched_terms(normalized, INTERNAL_RECORD_ACCESS_TERMS)
    if internal_matches:
        return build_refusal_result(
            reason=RefusalReason.INTERNAL_RECORD_ACCESS,
            matched=internal_matches,
        )

    clinical_matches = matched_terms(normalized, CLINICAL_OR_LEGAL_CONCLUSION_TERMS)
    if clinical_matches:
        return build_refusal_result(
            reason=RefusalReason.CLINICAL_OR_LEGAL_CONCLUSION,
            matched=clinical_matches,
        )

    return RefusalResult(refused=False)


def should_refuse(concern_text: str) -> bool:
    return evaluate_refusal(concern_text).refused


def get_refusal_message(concern_text: str) -> str | None:
    return evaluate_refusal(concern_text).message


def build_refusal_result(
    *,
    reason: RefusalReason,
    matched: list[str],
) -> RefusalResult:
    return RefusalResult(
        refused=True,
        reason=reason,
        message=build_refusal_message(reason),
        matched_terms=matched,
    )


def build_refusal_message(reason: RefusalReason) -> str:
    if reason == RefusalReason.EXTERNAL_DRUG_REFERENCE:
        return (
            "Unsupported in this synthetic proof of concept: the public synthetic "
            "corpus does not include Plumb's or another external drug reference. "
            "Do not infer or fabricate medication-specific adverse effects, "
            "contraindications, interactions, dose ranges, or species-specific "
            "toxicity from the available synthetic SOP evidence."
        )

    if reason == RefusalReason.INTERNAL_RECORD_ACCESS:
        return (
            "Unsupported in this synthetic proof of concept: this project does not "
            "access real compounding records, order pages, customer history, patient "
            "records, or inventory systems. Use only supplied synthetic summaries or "
            "state what a human reviewer should verify."
        )

    return (
        "Unsupported in this synthetic proof of concept: the request asks for a "
        "clinical, causality, or legal conclusion that this review-support workflow "
        "cannot determine. A human pharmacist or appropriate professional remains "
        "the final decision-maker."
    )


def matched_terms(text: str, terms: set[str]) -> list[str]:
    return sorted(term for term in terms if term in text)
