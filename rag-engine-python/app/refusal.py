from __future__ import annotations



from app.schemas import RefusalReason, RefusalResult



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
    "inventory system",
    "inventory systems",
    "stock status",
    "stock availability",
    "in stock",
    "back in stock",
    "out of stock",
    "available to order",
    "order it again",
    "when this medication will be back in stock",
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
            "I can’t safely answer that from the synthetic SOP evidence available here. "
            "This proof of concept does not include Plumb’s, a package insert, or another "
            "validated drug reference, so I should not make medication-specific claims about "
            "adverse effects, contraindications, interactions, dosing ranges, or species-specific "
            "toxicity. A pharmacist should verify that information against an appropriate external "
            "drug reference before making a recommendation."
        )

    if reason == RefusalReason.INTERNAL_RECORD_ACCESS:
        return (
            "I can’t verify that from the information available in this proof of concept. "
            "This system does not have access to real compounding records, order pages, customer "
            "history, patient records, or inventory systems. A pharmacist or reviewer should check "
            "the appropriate internal record and document what they confirm."
        )

    return (
        "I can’t make that determination from this review-support workflow alone. "
        "The available evidence does not support a final clinical, causality, or legal conclusion. "
        "This should be reviewed by a pharmacist or the appropriate responsible professional before "
        "any final decision is made."
    )


def matched_terms(text: str, terms: set[str]) -> list[str]:
    return sorted(term for term in terms if term in text)
