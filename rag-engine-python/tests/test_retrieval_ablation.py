from __future__ import annotations

import json
from pathlib import Path

from app.holdout_evaluate import build_parser
from app.retrieval_ablation import (
    parse_strategy_names,
    run_retrieval_ablation,
)


def chunk(source_id: str) -> dict[str, object]:
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
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        source_type: str | None = None,
    ) -> list[dict[str, object]]:
        self.queries.append(query)
        source_id = (
            "SOP-005"
            if "adverse event" in query.lower()
            else "SOP-004"
        )
        return [
            {
                "chunk": chunk(source_id),
                "score": 1.0,
                "matched_terms": ["test"],
            }
        ]


class StubNanoClient:
    model = "gpt-5-nano-test"

    def __init__(self) -> None:
        self.call_count = 0

    def complete_json(self, prompt: str) -> str:
        self.call_count += 1
        return json.dumps(
            {
                "search_text": (
                    "hospitalization adverse event escalation"
                ),
                "issue_tags": [
                    "adverse_event",
                    "pet_hospitalization",
                ],
                "required_topics": [
                    "adverse_event_review",
                    "severe_escalation",
                ],
                "excluded_topics": [],
            }
        )


def write_questions(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "question_id": "DEV-001",
                    "query": (
                        "The dog was hospitalized with blood "
                        "in the stool."
                    ),
                    "expected_source_ids": ["SOP-005"],
                    "forbidden_source_ids": ["SOP-002"],
                    "rationale": "Adverse-event review.",
                }
            ]
        ),
        encoding="utf-8",
    )


def test_strategy_parser_is_ordered_and_deduplicated() -> None:
    assert parse_strategy_names(
        "raw,nano_structured,raw"
    ) == [
        "raw",
        "nano_structured",
    ]


def test_ablation_changes_only_query_strategy_and_writes_artifacts(
    tmp_path: Path,
) -> None:
    questions_path = tmp_path / "questions.json"
    chunks_path = tmp_path / "chunks.jsonl"
    artifacts_root = tmp_path / "artifacts" / "runs"
    write_questions(questions_path)
    chunks_path.write_text("{}\n", encoding="utf-8")
    retriever = QuerySensitiveRetriever()
    nano_client = StubNanoClient()

    result = run_retrieval_ablation(
        questions_path=questions_path,
        chunks_path=chunks_path,
        strategy_names=[
            "raw",
            "deterministic_expansion",
            "nano_structured",
        ],
        run_id="test-run",
        artifacts_root=artifacts_root,
        retriever=retriever,
        nano_client=nano_client,
    )

    summaries = {
        summary["strategy"]: summary
        for summary in result["summaries"]
    }

    assert summaries["raw"]["hit_rate_at_k"] == 0.0
    assert (
        summaries["deterministic_expansion"][
            "hit_rate_at_k"
        ]
        == 1.0
    )
    assert (
        summaries["nano_structured"]["hit_rate_at_k"]
        == 1.0
    )
    assert nano_client.call_count == 1

    run_directory = artifacts_root / "test-run"
    assert (run_directory / "comparison.json").exists()
    assert (run_directory / "comparison.md").exists()
    assert (run_directory / "run_manifest.json").exists()
    assert (run_directory / "raw_results.json").exists()
    assert (
        run_directory
        / "deterministic_expansion_results.json"
    ).exists()
    assert (
        run_directory
        / "nano_structured_results.json"
    ).exists()
    assert (run_directory / "nano_intents.jsonl").exists()


def test_nano_cache_prevents_repeat_model_call(
    tmp_path: Path,
) -> None:
    questions_path = tmp_path / "questions.json"
    chunks_path = tmp_path / "chunks.jsonl"
    artifacts_root = tmp_path / "artifacts" / "runs"
    write_questions(questions_path)
    chunks_path.write_text("{}\n", encoding="utf-8")
    retriever = QuerySensitiveRetriever()
    first_client = StubNanoClient()

    run_retrieval_ablation(
        questions_path=questions_path,
        chunks_path=chunks_path,
        strategy_names=["nano_structured"],
        run_id="cache-run",
        artifacts_root=artifacts_root,
        retriever=retriever,
        nano_client=first_client,
    )

    second_client = StubNanoClient()
    result = run_retrieval_ablation(
        questions_path=questions_path,
        chunks_path=chunks_path,
        strategy_names=["nano_structured"],
        run_id="cache-run",
        artifacts_root=artifacts_root,
        retriever=retriever,
        nano_client=second_client,
    )

    summary = result["summaries"][0]

    assert first_client.call_count == 1
    assert second_client.call_count == 0
    assert summary["cache_hit_count"] == 1
    assert summary["model_call_count"] == 0


def test_cli_defaults_to_development_ablation() -> None:
    args = build_parser().parse_args(
        ["retrieval-ablation"]
    )

    assert args.command == "retrieval-ablation"
    assert (
        args.questions.name
        == "retrieval_questions_development.json"
    )
    assert args.top_k == 5
