import pytest

from app.refusal import (
    RefusalReason,
    build_refusal_message,
    evaluate_refusal,
    get_refusal_message,
    should_refuse,
)


def test_refuses_external_drug_reference_question() -> None:
    concern = "What exact adverse effects are listed in Plumb's for this medication?"

    result = evaluate_refusal(concern)

    assert result.refused is True
    assert result.reason == RefusalReason.EXTERNAL_DRUG_REFERENCE
    assert result.message is not None
    assert "synthetic SOP evidence" in result.message
    assert "validated drug reference" in result.message
    assert "medication-specific claims" in result.message
    assert "adverse effects" in result.message
    assert "dosing ranges" in result.message
    assert "species-specific toxicity" in result.message
    assert result.matched_terms


def test_should_refuse_external_reference_question() -> None:
    assert should_refuse("What contraindications are listed in the drug handbook?") is True


def test_refuses_internal_record_access_question() -> None:
    result = evaluate_refusal("Can you check the real compounding record and order page?")

    assert result.refused is True
    assert result.reason == RefusalReason.INTERNAL_RECORD_ACCESS
    assert result.message is not None
    assert "real compounding records" in result.message
    assert "inventory systems" in result.message


def test_refuses_clinical_or_legal_conclusion_question() -> None:
    result = evaluate_refusal("Did this medication cause the death and is Chewy liable?")

    assert result.reason == RefusalReason.CLINICAL_OR_LEGAL_CONCLUSION
    assert result.message is not None
    assert "clinical" in result.message.lower() or "causality" in result.message.lower()
    assert "legal" in result.message.lower()


def test_does_not_refuse_supported_synthetic_intake() -> None:
    result = evaluate_refusal("Dog vomited once after chicken flavored oral liquid.")

    assert result.refused is False
    assert result.reason is None
    assert result.message is None
    assert result.matched_terms == []


def test_get_refusal_message_returns_message_for_unsupported_request() -> None:
    message = get_refusal_message("What does Plumb's say about this medication?")

    assert message is not None
    assert "synthetic" in message.lower()
    assert "external drug reference" in message.lower()


def test_get_refusal_message_returns_none_for_supported_request() -> None:
    message = get_refusal_message("Dog refused flavored oral liquid.")

    assert message is None


def test_evaluate_refusal_rejects_blank_text() -> None:
    with pytest.raises(ValueError, match="concern_text must not be empty"):
        evaluate_refusal("   ")


def test_build_refusal_message_external_reference_is_direct() -> None:
    message = build_refusal_message(RefusalReason.EXTERNAL_DRUG_REFERENCE)

    assert message.startswith("I can’t safely answer")
    assert "synthetic SOP evidence" in message
    assert "validated drug reference" in message
    assert "medication-specific claims" in message
    assert "appropriate external drug reference" in message


def test_refuses_back_in_stock_question() -> None:
    result = evaluate_refusal(
        "A customer wants to know when this medication will be back in stock so they can order it again."
    )

    assert result.refused is True
    assert result.reason == RefusalReason.INTERNAL_RECORD_ACCESS


def test_refuses_available_to_order_question() -> None:
    result = evaluate_refusal(
        "Can you check whether this compounded medication is available to order?"
    )

    assert result.refused is True
    assert result.reason == RefusalReason.INTERNAL_RECORD_ACCESS