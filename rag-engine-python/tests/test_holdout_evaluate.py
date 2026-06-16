import json
from pathlib import Path

import pytest

from app.holdout_evaluate import (
    build_parser,
    evaluate_retrieval_holdout,
    freeze_holdout_files,
    load_retrieval_holdout_questions,
)
from app.retrieval import ChunkRecord, SearchResult


class StubRetriever:
    def __init__(self, results: list[SearchResult]) -> None:
        self._results = results

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        source_type: str | None = None,
    ) -> list[SearchResult]:
        return self._results[:top_k]


def test_load_retrieval_holdout_preserves_negative_constraints(
    tmp_path: Path,
) -> None:
    path = tmp_path / "retrieval.json"
    path.write_text(
        json.dumps(
            [
                {
                    "question_id": "RET-H-001",
                    "query": "dog vomited after oral liquid",
                    "expected_source_ids": ["SOP-005"],
                    "forbidden_source_ids": ["SOP-002"],
                    "rationale": "Adverse-event guidance should outrank BUD guidance.",
                }
            ]
        ),
        encoding="utf-8",
    )

    questions = load_retrieval_holdout_questions(path)

    assert questions[0]["forbidden_source_ids"] == ["SOP-002"]
    assert "Adverse-event" in questions[0]["rationale"]


def test_load_retrieval_holdout_rejects_expected_forbidden_overlap(
    tmp_path: Path,
) -> None:
    path = tmp_path / "retrieval.json"
    path.write_text(
        json.dumps(
            [
                {
                    "question_id": "RET-H-001",
                    "query": "dog vomited",
                    "expected_source_ids": ["SOP-005"],
                    "forbidden_source_ids": ["SOP-005"],
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="expect and forbid"):
        load_retrieval_holdout_questions(path)


def test_evaluate_retrieval_holdout_flags_forbidden_source() -> None:
    questions = [
        {
            "question_id": "RET-H-001",
            "query": "dog vomited",
            "expected_source_ids": ["SOP-005"],
            "forbidden_source_ids": ["SOP-002"],
            "rationale": "BUD guidance is irrelevant.",
        }
    ]
    retriever = StubRetriever(
        [
            search_result("SOP-002", score=10.0),
            search_result("SOP-005", score=9.0),
        ]
    )

    result = evaluate_retrieval_holdout(
        questions,
        top_k=5,
        retriever=retriever,
    )

    assert result["hit_rate_at_k"] == 1.0
    assert result["mean_reciprocal_rank"] == 0.5
    assert result["negative_constraint_pass_rate"] == 0.0
    assert result["forbidden_hit_question_ids"] == ["RET-H-001"]
    assert result["question_results"][0]["forbidden_source_hits"] == [
        "SOP-002"
    ]


def test_freeze_holdout_files_writes_hash_manifest(
    tmp_path: Path,
) -> None:
    extraction_path = tmp_path / "extraction.json"
    extraction_path.write_text(
        json.dumps([valid_extraction_case()]),
        encoding="utf-8",
    )
    retrieval_path = tmp_path / "retrieval.json"
    retrieval_path.write_text(
        json.dumps(
            [
                {
                    "question_id": "RET-H-001",
                    "query": "dog vomited",
                    "expected_source_ids": ["SOP-005"],
                    "forbidden_source_ids": [],
                }
            ]
        ),
        encoding="utf-8",
    )
    manifest_path = tmp_path / "manifest.json"

    manifest = freeze_holdout_files(
        extraction_cases_path=extraction_path,
        retrieval_questions_path=retrieval_path,
        manifest_path=manifest_path,
    )

    assert manifest_path.exists()
    assert len(manifest["files"]) == 2
    assert all(len(item["sha256"]) == 64 for item in manifest["files"])
    assert [item["item_count"] for item in manifest["files"]] == [1, 1]


def test_parser_accepts_custom_holdout_paths() -> None:
    args = build_parser().parse_args(
        [
            "validate",
            "--extraction-cases",
            "custom-extraction.json",
            "--retrieval-questions",
            "custom-retrieval.json",
        ]
    )

    assert args.extraction_cases == Path("custom-extraction.json")
    assert args.retrieval_questions == Path("custom-retrieval.json")


def valid_extraction_case() -> dict[str, object]:
    return {
        "case_id": "EXT-H-001",
        "concern_text": "Dog vomited.",
        "reviewer_note": "No hospitalization. Dose unknown.",
        "expected_review_summary": {
            "record_review_result": "no_discrepancy_found",
            "lot_batch_pattern_summary": "unavailable",
            "inventory_inspection_result": "not_checked",
            "customer_context_summary": "Dog vomited.",
            "api_reference_review_result": "not_needed",
            "missing_information": ["Exact dose administered"],
            "evidence_limitations": [],
            "severe_triggers_observed": [],
        },
        "expected_unresolved_field_names": ["dose_administered"],
    }


def search_result(
    source_id: str,
    *,
    score: float,
) -> SearchResult:
    chunk: ChunkRecord = {
        "chunk_id": f"{source_id}::section",
        "source_id": source_id,
        "source_file": f"{source_id.lower()}.md",
        "source_title": f"{source_id} Title",
        "source_type": "sop",
        "section_heading": "Section",
        "process_area": "compounding_quality",
        "version": "1.0",
        "effective_date": "2025-01-01",
        "synthetic": True,
        "text": "Synthetic chunk text.",
    }

    return {
        "chunk": chunk,
        "score": score,
        "matched_terms": ["synthetic"],
    }
