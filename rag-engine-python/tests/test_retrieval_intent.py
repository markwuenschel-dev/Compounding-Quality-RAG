from __future__ import annotations

import json

import pytest

from app.retrieval_intent import (
    INTENT_SEARCH_TERMS,
    NanoIntentDetector,
    RetrievalIntent,
    RetrievalIntentTag,
    RuleIntentDetector,
    SemanticIntentTag,
    SemanticRetrievalIntent,
    UnknownIntentTagError,
    build_nano_intent_prompt,
    derive_retrieval_intent,
    map_intent_to_search_text,
)


class StubClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.prompts: list[str] = []

    def complete_json(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return json.dumps(self.payload)


def detect(text: str) -> set[SemanticIntentTag]:
    return set(RuleIntentDetector().detect(text).tags)


def derive(*tags: SemanticIntentTag) -> set[RetrievalIntentTag]:
    semantic = SemanticRetrievalIntent(tags=list(tags))
    return set(derive_retrieval_intent(semantic).tags)


def test_every_derived_tag_has_a_mapper_entry() -> None:
    assert set(INTENT_SEARCH_TERMS) == set(RetrievalIntentTag)


def test_rule_detector_returns_semantic_tags_only() -> None:
    tags = detect("The dog was hospitalized after vomiting and bloody stool.")

    assert tags == {
        SemanticIntentTag.ADVERSE_EVENT,
        SemanticIntentTag.PET_HOSPITALIZATION,
        SemanticIntentTag.GASTROINTESTINAL,
    }


def test_hospitalization_derives_review_and_escalation() -> None:
    tags = derive(SemanticIntentTag.PET_HOSPITALIZATION)

    assert {
        RetrievalIntentTag.ADVERSE_EVENT,
        RetrievalIntentTag.PET_HOSPITALIZATION,
        RetrievalIntentTag.ADVERSE_EVENT_REVIEW,
        RetrievalIntentTag.SEVERE_ESCALATION,
    } <= tags


def test_negated_hospitalization_does_not_become_semantic_fact() -> None:
    tags = detect(
        "The dog looked winded after the dose but was never hospitalized."
    )

    assert SemanticIntentTag.RESPIRATORY_CONTEXT in tags
    assert SemanticIntentTag.PET_HOSPITALIZATION not in tags


def test_respiratory_context_derives_ade_review_and_outreach() -> None:
    tags = derive(SemanticIntentTag.RESPIRATORY_CONTEXT)

    assert {
        RetrievalIntentTag.ADVERSE_EVENT,
        RetrievalIntentTag.ADVERSE_EVENT_REVIEW,
        RetrievalIntentTag.PHARMACIST_OUTREACH,
    } <= tags


def test_quality_concerns_derive_full_quality_workflow() -> None:
    device = derive(SemanticIntentTag.DEVICE_CONCERN)
    appearance = derive(SemanticIntentTag.APPEARANCE_CONCERN)
    quantity = derive(SemanticIntentTag.QUANTITY_DISCREPANCY)

    for tags in (device, appearance, quantity):
        assert RetrievalIntentTag.QUALITY_REVIEW in tags

    assert RetrievalIntentTag.TREND_REVIEW in device
    assert RetrievalIntentTag.TREND_REVIEW in appearance
    assert RetrievalIntentTag.TREND_REVIEW in quantity
    assert RetrievalIntentTag.LOT_BATCH_REVIEW in appearance
    assert RetrievalIntentTag.ADMINISTRATION_REVIEW in quantity


def test_disclosure_workflow_is_derived_from_supplier_semantics() -> None:
    tags = derive(SemanticIntentTag.SUPPLIER_QUESTION)

    assert {
        RetrievalIntentTag.FRONTLINE_PHARMACIST_RESPONSE,
        RetrievalIntentTag.DISCLOSURE_BOUNDARY,
        RetrievalIntentTag.PUBLIC_CORPUS_BOUNDARY,
    } <= tags


def test_reference_workflow_is_derived_from_bud_semantics() -> None:
    tags = derive(SemanticIntentTag.BUD_QUESTION)

    assert {
        RetrievalIntentTag.REFERENCE_REVIEW,
        RetrievalIntentTag.REFERENCE_BOUNDARY,
    } <= tags


def test_short_pen_token_does_not_match_inside_other_words() -> None:
    assert SemanticIntentTag.DEVICE_CONCERN not in detect(
        "The oral oil suspension smells sour."
    )
    assert SemanticIntentTag.DEVICE_CONCERN not in detect(
        "The customer spent several minutes discussing shipping delays."
    )


def test_manufacturer_reporting_is_not_supplier_request() -> None:
    tags = detect(
        "The pet became weak after the dose and the owner will not report to the manufacturer."
    )

    assert SemanticIntentTag.SUPPLIER_QUESTION not in tags
    assert SemanticIntentTag.NEUROLOGIC_SIGNS in tags

def test_supplier_question_detects_ask_about_source_phrasing() -> None:
    tags = detect(
        "The customer is reaching out to ask about where we source "
        "the ingredients from."
    )

    assert SemanticIntentTag.SUPPLIER_QUESTION in tags

def test_food_timing_context_is_not_administration_question() -> None:
    tags = detect(
        "The first dose was given twenty minutes prior to eating and weakness began later."
    )

    assert SemanticIntentTag.ADMINISTRATION_QUESTION not in tags
    assert SemanticIntentTag.NEUROLOGIC_SIGNS in tags


def test_flavor_composition_and_rejection_remain_separate() -> None:
    composition = detect(
        "The customer wants every inactive component and asks whether the flavor contains animal-derived oil."
    )
    rejection = detect(
        "The cat drools, shakes her head, and tries to spit the liquid out."
    )

    assert SemanticIntentTag.INGREDIENT_QUESTION in composition
    assert SemanticIntentTag.PALATABILITY_CONCERN not in composition
    assert SemanticIntentTag.PALATABILITY_CONCERN in rejection
    assert SemanticIntentTag.INGREDIENT_QUESTION not in rejection


def test_nano_detector_accepts_semantic_tags_only() -> None:
    client = StubClient(
        {"tags": ["Adverse Event", "neurologic-signs", "Adverse Event"]}
    )

    intent = NanoIntentDetector(client).detect(
        "The pet became weak and wobbly."
    )

    assert intent.tags == [
        SemanticIntentTag.ADVERSE_EVENT,
        SemanticIntentTag.NEUROLOGIC_SIGNS,
    ]
    assert "trend_review" not in client.prompts[0]
    assert "Do not return review" in client.prompts[0]


def test_nano_detector_rejects_workflow_tag() -> None:
    client = StubClient({"tags": ["adverse_event", "trend_review"]})

    with pytest.raises(UnknownIntentTagError):
        NanoIntentDetector(client).detect("The pet vomited.")


def test_nano_prompt_lists_exact_semantic_vocabulary() -> None:
    prompt = build_nano_intent_prompt("Concern")
    allowed_section = prompt.split(
        "Allowed semantic tags:\n",
        maxsplit=1,
    )[1].split("\n\nRules:", maxsplit=1)[0]

    assert allowed_section.split(", ") == [
        tag.value for tag in SemanticIntentTag
    ]
    for workflow_tag in (
        "adverse_event_review",
        "quality_review",
        "trend_review",
        "reference_boundary",
    ):
        assert workflow_tag not in allowed_section


def test_mapper_uses_derived_workflow_terms() -> None:
    intent = derive_retrieval_intent(
        SemanticRetrievalIntent(tags=[SemanticIntentTag.DEVICE_CONCERN])
    )

    search_text = map_intent_to_search_text(
        "The pen clicks but nothing comes out.",
        intent,
    )

    assert "dispensing device" in search_text
    assert "quality review" in search_text
    assert "trend review" in search_text


def test_mapper_preserves_original_text() -> None:
    original = "The pet was weak after the dose."
    intent = RetrievalIntent(
        tags=[
            RetrievalIntentTag.ADVERSE_EVENT,
            RetrievalIntentTag.NEUROLOGIC_SIGNS,
        ]
    )

    assert map_intent_to_search_text(original, intent).startswith(original)
