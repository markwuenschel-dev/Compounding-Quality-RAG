from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.retrieval_intent import (
    INTENT_SCHEMA_VERSION,
    NanoIntentDetector,
    RetrievalIntentTag,
)
from app.retrieval_query_strategy import (
    BuiltRetrievalQuery,
    DeterministicExpansionStrategy,
    NanoIntentQueryStrategy,
    RawQueryStrategy,
    RetrievalIntentCache,
    RuleIntentQueryStrategy,
)


class StubJsonClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def complete_json(self, prompt: str) -> str:
        return json.dumps(self.payload)


def test_raw_strategy_preserves_original_query() -> None:
    query = RawQueryStrategy().build(
        "The dog vomited after the medication."
    )

    assert query.strategy == "raw"
    assert query.search_text == query.original_text
    assert query.intent is None


def test_legacy_deterministic_strategy_remains_comparator() -> None:
    query = DeterministicExpansionStrategy().build(
        "The dog was hospitalized after vomiting."
    )

    assert query.strategy == "deterministic_expansion"
    assert "adverse event" in query.search_text
    assert "pet_hospitalization" in query.legacy_issue_tags
    assert query.intent is None


def test_legacy_device_topics_use_quality_and_trend_without_device_review() -> None:
    query = DeterministicExpansionStrategy().build(
        "The pen clicks but nothing comes out."
    )

    assert "quality_review" in query.legacy_required_topics
    assert "trend_review" in query.legacy_required_topics
    assert "device_review" not in query.legacy_required_topics


def test_rule_intent_strategy_uses_shared_mapper() -> None:
    query = RuleIntentQueryStrategy().build(
        "The pet had difficulty walking and weakness after the dose."
    )

    assert query.strategy == "rule_intent"
    assert query.intent is not None
    assert RetrievalIntentTag.NEUROLOGIC_SIGNS in query.intent.tags
    assert "neurologic signs" in query.search_text


def test_nano_intent_strategy_does_not_accept_search_text() -> None:
    strategy = NanoIntentQueryStrategy(
        NanoIntentDetector(
            StubJsonClient(
                {
                    "tags": [
                        "adverse_event",
                        "pet_hospitalization",
                    ]
                }
            )
        )
    )

    query = strategy.build("The pet was hospitalized.")

    assert query.strategy == "nano_intent"
    assert query.intent is not None
    assert "hospitalization" in query.search_text


def test_query_contract_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        BuiltRetrievalQuery.model_validate(
            {
                "original_text": "Concern",
                "search_text": "Concern",
                "strategy": "raw",
                "unexpected": True,
            }
        )


def test_cache_round_trip_and_input_invalidation(tmp_path) -> None:
    cache_path = tmp_path / "nano_intents.jsonl"
    cache = RetrievalIntentCache(cache_path)
    semantic_intent = NanoIntentDetector(
        StubJsonClient({"tags": ["adverse_event"]})
    ).detect("Original concern")

    cache.put(
        question_id="Q-001",
        concern_text="Original concern",
        model="gpt-5-nano",
        semantic_intent=semantic_intent,
    )
    cache.flush()
    loaded = RetrievalIntentCache(cache_path)

    assert loaded.get(
        question_id="Q-001",
        concern_text="Original concern",
        model="gpt-5-nano",
    ) == semantic_intent
    assert loaded.get(
        question_id="Q-001",
        concern_text="Changed concern",
        model="gpt-5-nano",
    ) is None


def test_cache_invalidates_when_schema_version_changes(tmp_path) -> None:
    cache_path = tmp_path / "nano_intents.jsonl"
    cache = RetrievalIntentCache(cache_path)
    semantic_intent = NanoIntentDetector(
        StubJsonClient({"tags": ["adverse_event"]})
    ).detect("Concern")

    cache.put(
        question_id="Q-001",
        concern_text="Concern",
        model="gpt-5-nano",
        semantic_intent=semantic_intent,
        intent_schema_version=INTENT_SCHEMA_VERSION,
    )
    cache.flush()

    loaded = RetrievalIntentCache(cache_path)
    cached = loaded.get(
        question_id="Q-001",
        concern_text="Concern",
        model="gpt-5-nano",
        intent_schema_version=INTENT_SCHEMA_VERSION,
    )
    stale = loaded.get(
        question_id="Q-001",
        concern_text="Concern",
        model="gpt-5-nano",
        intent_schema_version="different-version",
    )

    assert cached == semantic_intent
    assert stale is None
