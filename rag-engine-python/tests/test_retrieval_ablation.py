from __future__ import annotations

import json
from pathlib import Path

from app.holdout_evaluate import build_parser
from app.retrieval import ChunkRecord, SearchResult
from app.retrieval_ablation import (
    StrategyQuestionResult,
    calculate_intent_metrics,
    calculate_semantic_intent_metrics,
    parse_strategy_names,
    run_retrieval_ablation,
)


def chunk(source_id: str) -> ChunkRecord:
    return {
        "chunk_id": f"{source_id}-001",
        "source_id": source_id,
        "source_file": f"{source_id}.md",
        "source_title": source_id,
        "source_type": "sop",
        "section_heading": "Test",
        "process_area": "test",
        "version": "1",
        "effective_date": "2026-01-01",
        "synthetic": True,
        "text": "test",
    }


class QuerySensitiveRetriever:
    def __init__(self, include_forbidden: bool = False) -> None:
        self.queries: list[str] = []
        self.include_forbidden = include_forbidden

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        source_type: str | None = None,
    ) -> list[SearchResult]:
        self.queries.append(query)
        source_id = (
            "SOP-005"
            if "adverse event" in query.lower()
            else "SOP-004"
        )
        results: list[SearchResult] = [
            {
                "chunk": chunk(source_id),
                "score": 1.0,
                "matched_terms": ["test"],
            }
        ]
        if self.include_forbidden:
            results.insert(
                0,
                {
                    "chunk": chunk("SOP-002"),
                    "score": 2.0,
                    "matched_terms": ["test"],
                },
            )
        return results[:top_k]


class StubNanoClient:
    model = "gpt-5-nano-test"

    def __init__(self, payload: dict[str, object] | None = None) -> None:
        self.call_count = 0
        self.payload = payload or {
            "tags": [
                "adverse_event",
                "pet_hospitalization",
                "gastrointestinal",
            ]
        }

    def complete_json(self, prompt: str) -> str:
        self.call_count += 1
        return json.dumps(self.payload)


class InvalidNanoClient:
    model = "gpt-5-nano-test"

    def __init__(self) -> None:
        self.call_count = 0

    def complete_json(self, prompt: str) -> str:
        self.call_count += 1
        return json.dumps({"tags": ["trend_review"]})


def write_questions(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "question_id": "DEV-001",
                    "query": (
                        "The dog was hospitalized after vomiting and bloody stool."
                    ),
                    "expected_source_ids": ["SOP-005"],
                    "forbidden_source_ids": ["SOP-002"],
                    "expected_semantic_intent_tags": [
                        "adverse_event",
                        "pet_hospitalization",
                        "gastrointestinal",
                    ],
                    "expected_intent_tags": [
                        "adverse_event",
                        "pet_hospitalization",
                        "gastrointestinal",
                        "adverse_event_review",
                        "severe_escalation",
                    ],
                    "rationale": "Adverse-event review.",
                }
            ]
        ),
        encoding="utf-8",
    )


def question_result(
    *,
    predicted_semantic: list[str],
    expected_semantic: list[str],
    semantic_exact: bool,
    predicted: list[str],
    expected: list[str],
    exact: bool,
) -> StrategyQuestionResult:
    return {
        "question_id": "Q-1",
        "original_query": "x",
        "search_text": "x",
        "predicted_semantic_intent_tags": predicted_semantic,
        "expected_semantic_intent_tags": expected_semantic,
        "semantic_intent_exact_match": semantic_exact,
        "predicted_intent_tags": predicted,
        "expected_intent_tags": expected,
        "intent_exact_match": exact,
        "expected_source_ids": [],
        "forbidden_source_ids": [],
        "retrieved_source_ids": [],
        "hit": False,
        "reciprocal_rank": 0.0,
        "forbidden_source_hits": [],
        "negative_constraints_passed": True,
        "used_fallback": False,
    }


def test_strategy_parser_is_ordered_and_deduplicated() -> None:
    assert parse_strategy_names(
        "raw,nano_intent,rule_intent,raw"
    ) == ["raw", "nano_intent", "rule_intent"]


def test_ablation_scores_semantic_and_derived_intents_separately(
    tmp_path: Path,
) -> None:
    questions_path = tmp_path / "questions.json"
    chunks_path = tmp_path / "chunks.jsonl"
    artifacts_root = tmp_path / "artifacts" / "runs"
    write_questions(questions_path)
    chunks_path.write_text("{}\n", encoding="utf-8")
    nano_client = StubNanoClient()

    result = run_retrieval_ablation(
        questions_path=questions_path,
        chunks_path=chunks_path,
        strategy_names=["rule_intent", "nano_intent"],
        run_id="test-run",
        artifacts_root=artifacts_root,
        retriever=QuerySensitiveRetriever(),
        nano_client=nano_client,
    )

    summaries = {
        summary["strategy"]: summary
        for summary in result["summaries"]
    }
    for strategy in ("rule_intent", "nano_intent"):
        summary = summaries[strategy]
        assert summary["semantic_intent_micro_precision"] == 1.0
        assert summary["semantic_intent_micro_recall"] == 1.0
        assert summary["semantic_intent_exact_match_rate"] == 1.0
        assert summary["intent_exact_match_rate"] == 1.0

    row = json.loads(
        (artifacts_root / "test-run" / "nano_intent_results.json")
        .read_text(encoding="utf-8")
    )["question_results"][0]
    assert row["predicted_semantic_intent_tags"] == [
        "adverse_event",
        "pet_hospitalization",
        "gastrointestinal",
    ]
    assert "adverse_event_review" in row["predicted_intent_tags"]


def test_rule_intent_preserves_negative_constraints(tmp_path: Path) -> None:
    questions_path = tmp_path / "questions.json"
    chunks_path = tmp_path / "chunks.jsonl"
    write_questions(questions_path)
    chunks_path.write_text("{}\n", encoding="utf-8")

    result = run_retrieval_ablation(
        questions_path=questions_path,
        chunks_path=chunks_path,
        strategy_names=["rule_intent"],
        run_id="negative-run",
        artifacts_root=tmp_path / "artifacts",
        retriever=QuerySensitiveRetriever(include_forbidden=True),
    )

    assert result["summaries"][0][
        "negative_constraint_pass_rate"
    ] == 0.0


def test_nano_cache_prevents_repeat_model_call(tmp_path: Path) -> None:
    questions_path = tmp_path / "questions.json"
    chunks_path = tmp_path / "chunks.jsonl"
    artifacts_root = tmp_path / "artifacts" / "runs"
    write_questions(questions_path)
    chunks_path.write_text("{}\n", encoding="utf-8")

    first_client = StubNanoClient()
    run_retrieval_ablation(
        questions_path=questions_path,
        chunks_path=chunks_path,
        strategy_names=["nano_intent"],
        run_id="cache-run",
        artifacts_root=artifacts_root,
        retriever=QuerySensitiveRetriever(),
        nano_client=first_client,
    )

    second_client = StubNanoClient()
    result = run_retrieval_ablation(
        questions_path=questions_path,
        chunks_path=chunks_path,
        strategy_names=["nano_intent"],
        run_id="cache-run",
        artifacts_root=artifacts_root,
        retriever=QuerySensitiveRetriever(),
        nano_client=second_client,
    )

    assert first_client.call_count == 1
    assert second_client.call_count == 0
    assert result["summaries"][0]["cache_hit_count"] == 1


def test_fallback_is_not_cached_as_nano_output(tmp_path: Path) -> None:
    questions_path = tmp_path / "questions.json"
    chunks_path = tmp_path / "chunks.jsonl"
    artifacts_root = tmp_path / "artifacts" / "runs"
    write_questions(questions_path)
    chunks_path.write_text("{}\n", encoding="utf-8")

    invalid_client = InvalidNanoClient()
    first = run_retrieval_ablation(
        questions_path=questions_path,
        chunks_path=chunks_path,
        strategy_names=["nano_intent"],
        run_id="fallback-run",
        artifacts_root=artifacts_root,
        retriever=QuerySensitiveRetriever(),
        nano_client=invalid_client,
    )

    valid_client = StubNanoClient()
    second = run_retrieval_ablation(
        questions_path=questions_path,
        chunks_path=chunks_path,
        strategy_names=["nano_intent"],
        run_id="fallback-run",
        artifacts_root=artifacts_root,
        retriever=QuerySensitiveRetriever(),
        nano_client=valid_client,
    )

    assert first["summaries"][0]["fallback_count"] == 1
    assert valid_client.call_count == 1
    assert second["summaries"][0]["cache_hit_count"] == 0
    assert second["summaries"][0]["cache_miss_count"] == 1


def test_semantic_metrics_use_semantic_fields_not_derived_fields() -> None:
    results = [
        question_result(
            predicted_semantic=["device_concern"],
            expected_semantic=["appearance_concern"],
            semantic_exact=False,
            predicted=[
                "device_concern",
                "quality_review",
                "trend_review",
            ],
            expected=[
                "device_concern",
                "quality_review",
                "trend_review",
            ],
            exact=True,
        )
    ]

    semantic = calculate_semantic_intent_metrics(results)
    derived = calculate_intent_metrics(results)

    assert semantic["precision"] == 0.0
    assert semantic["recall"] == 0.0
    assert semantic["exact_match_rate"] == 0.0
    assert derived["precision"] == 1.0
    assert derived["recall"] == 1.0
    assert derived["exact_match_rate"] == 1.0


def test_cli_defaults_to_controlled_intent_ablation() -> None:
    args = build_parser().parse_args(["retrieval-ablation"])

    assert args.command == "retrieval-ablation"
    assert args.questions.name == "retrieval_questions_development.json"
    assert args.top_k == 5
    assert (
        args.strategies
        == "raw,deterministic_expansion,rule_intent,nano_intent"
    )
