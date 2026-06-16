from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.retrieval_query_strategy import (
    DeterministicExpansionStrategy,
    NanoStructuredQueryStrategy,
    RawQueryStrategy,
    RetrievalIntentCache,
    RetrievalQueryIntent,
)


class StubJsonClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.prompts: list[str] = []

    def complete_json(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return json.dumps(self.payload)


def test_raw_strategy_preserves_original_query() -> None:
    intent = RawQueryStrategy().build(
        "The dog vomited after the medication."
    )

    assert intent.strategy == "raw"
    assert intent.search_text == intent.original_text
    assert intent.issue_tags == []


def test_deterministic_strategy_expands_hospitalization_and_gi_context() -> None:
    intent = DeterministicExpansionStrategy().build(
        "The dog was hospitalized after vomiting and blood in the stool."
    )

    assert intent.strategy == "deterministic_expansion"
    assert "adverse event" in intent.search_text
    assert "pet_hospitalization" in intent.issue_tags
    assert "severe_escalation" in intent.required_topics


def test_shortness_of_breath_does_not_create_automatic_severe_escalation() -> None:
    intent = DeterministicExpansionStrategy().build(
        "The pet looked short of breath after the first dose."
    )

    assert "respiratory_context" in intent.issue_tags
    assert "automatic_severe_escalation" in intent.excluded_topics
    assert "severe_escalation" not in intent.required_topics


def test_disclosure_request_gets_boundary_terms() -> None:
    intent = DeterministicExpansionStrategy().build(
        "Where do you source the ingredients and who is the manufacturer?"
    )

    assert "supplier_question" in intent.issue_tags
    assert "public_corpus_boundary" in intent.required_topics
    assert "leadership_escalation" in intent.excluded_topics


def test_nano_strategy_validates_and_normalizes_structured_output() -> None:
    client = StubJsonClient(
        {
            "search_text": "hospitalization adverse event escalation",
            "issue_tags": [
                "Adverse Event",
                "pet-hospitalization",
                "Adverse Event",
            ],
            "required_topics": ["Severe Escalation"],
            "excluded_topics": [],
        }
    )

    intent = NanoStructuredQueryStrategy(client).build(
        "The pet was hospitalized."
    )

    assert intent.strategy == "nano_structured"
    assert intent.issue_tags == [
        "adverse_event",
        "pet_hospitalization",
    ]
    assert intent.required_topics == ["severe_escalation"]
    assert len(client.prompts) == 1


def test_nano_strategy_rejects_blank_search_text() -> None:
    client = StubJsonClient(
        {
            "search_text": " ",
            "issue_tags": [],
            "required_topics": [],
            "excluded_topics": [],
        }
    )

    with pytest.raises(ValueError):
        NanoStructuredQueryStrategy(client).build(
            "The pet was hospitalized."
        )


def test_intent_contract_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        RetrievalQueryIntent.model_validate(
            {
                "original_text": "Concern",
                "search_text": "Concern",
                "issue_tags": [],
                "required_topics": [],
                "excluded_topics": [],
                "strategy": "raw",
                "unexpected": True,
            }
        )


def test_cache_round_trip_and_input_invalidation(tmp_path) -> None:
    cache_path = tmp_path / "nano_intents.jsonl"
    cache = RetrievalIntentCache(cache_path)
    intent = RawQueryStrategy().build("Original concern")

    cache.put(
        question_id="Q-001",
        concern_text="Original concern",
        model="gpt-5-nano",
        intent=intent,
    )
    cache.flush()

    loaded = RetrievalIntentCache(cache_path)

    assert loaded.get(
        question_id="Q-001",
        concern_text="Original concern",
        model="gpt-5-nano",
    ) == intent
    assert loaded.get(
        question_id="Q-001",
        concern_text="Changed concern",
        model="gpt-5-nano",
    ) is None

def test_nano_strategy_preserves_original_text_and_accepts_json_fence() -> None:
    class FencedClient:
        def complete_json(self, prompt: str) -> str:
            return """```json
{
  "search_text": "hospitalization adverse event",
  "issue_tags": ["adverse_event"],
  "required_topics": ["adverse_event_review"],
  "excluded_topics": []
}
```"""

    intent = NanoStructuredQueryStrategy(FencedClient()).build(
        "The pet was hospitalized."
    )

    assert intent.search_text.startswith(
        "The pet was hospitalized."
    )
    assert (
        "Retrieval concepts: hospitalization adverse event"
        in intent.search_text
    )

