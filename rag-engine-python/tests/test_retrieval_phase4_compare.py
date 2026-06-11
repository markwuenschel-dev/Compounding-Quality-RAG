from __future__ import annotations

from pathlib import Path

from app.retrieval_compare import (
    RetrievalComparisonResult,
    RetrieverComparisonSummary,
    best_retriever_names,
    build_phase4_retrievers,
    find_summary,
    format_qualitative_notes,
    format_retrieval_comparison_markdown,
    load_and_compare_phase4_retrievers,
    write_retrieval_comparison_report,
)
from app.retrieval_evaluate import DEFAULT_RETRIEVAL_QUESTIONS_PATH


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "index" / "chunks.jsonl"


def test_build_phase4_retrievers_returns_keyword_embedding_and_hybrid() -> None:
    retrievers = build_phase4_retrievers(
        chunks_path=CHUNKS_PATH,
        embedding_dimensions=128,
    )

    assert list(retrievers.keys()) == ["keyword", "embedding", "hybrid"]
    assert hasattr(retrievers["keyword"], "search")
    assert hasattr(retrievers["embedding"], "search")
    assert hasattr(retrievers["hybrid"], "search")


def test_load_and_compare_phase4_retrievers_runs_end_to_end() -> None:
    result = load_and_compare_phase4_retrievers(
        questions_path=DEFAULT_RETRIEVAL_QUESTIONS_PATH,
        chunks_path=CHUNKS_PATH,
        top_k=5,
        embedding_dimensions=128,
    )

    assert result["question_count"] > 0
    assert result["top_k"] == 5
    assert [summary["retriever_name"] for summary in result["summaries"]] == [
        "keyword",
        "embedding",
        "hybrid",
    ]

    for summary in result["summaries"]:
        assert 0 <= summary["hit_rate_at_k"] <= 1
        assert 0 <= summary["mean_reciprocal_rank"] <= 1
        assert summary["total_questions"] == result["question_count"]
        assert summary["top_k"] == result["top_k"]


def test_phase4_comparison_preserves_custom_top_k() -> None:
    result = load_and_compare_phase4_retrievers(
        questions_path=DEFAULT_RETRIEVAL_QUESTIONS_PATH,
        chunks_path=CHUNKS_PATH,
        top_k=3,
        embedding_dimensions=64,
    )

    assert result["top_k"] == 3
    assert all(summary["top_k"] == 3 for summary in result["summaries"])


def test_best_retriever_names_returns_all_tied_retrievers() -> None:
    summaries = sample_summaries()

    best = best_retriever_names(
        summaries,
        metric_name="hit_rate_at_k",
    )

    assert best == ["embedding", "hybrid"]


def test_find_summary_returns_named_summary() -> None:
    summary = find_summary(sample_summaries(), "hybrid")

    assert summary is not None
    assert summary["retriever_name"] == "hybrid"


def test_find_summary_returns_none_for_missing_summary() -> None:
    assert find_summary(sample_summaries(), "missing") is None


def test_format_qualitative_notes_mentions_best_metrics_and_failure_deltas() -> None:
    notes = format_qualitative_notes(sample_result())
    
    for note in notes:
        print(note)
    
    assert "- Best hit_rate@k: embedding, hybrid." in notes
    assert "- Best MRR: hybrid." in notes
    assert (
        "- Keyword failed questions not failed by embedding: RET-002."
        in notes
    )
    assert (
        "- Embedding failed questions not failed by keyword: RET-003."
        in notes
    )
    assert (
        "- Hybrid failures not present in keyword baseline: None."
        in notes
    )
    assert (
        "- Keyword failures resolved by hybrid: RET-002."
        in notes
    )


def test_phase4_markdown_includes_all_retrievers_and_notes() -> None:
    markdown = format_retrieval_comparison_markdown(sample_result())

    assert "# Retrieval Comparison Report" in markdown
    assert "| keyword | 0.750 | 0.500 | RET-002 | 0.100000 |" in markdown
    assert "| embedding | 0.875 | 0.625 | RET-003 | 0.200000 |" in markdown
    assert "| hybrid | 0.875 | 0.750 | None | 0.300000 |" in markdown
    assert "## Qualitative Notes" in markdown
    assert "## Interpretation Guardrails" in markdown
    assert "Hashing embeddings are a local deterministic vector baseline" in markdown


def test_write_phase4_comparison_report_writes_markdown(tmp_path: Path) -> None:
    output_path = tmp_path / "retrieval_comparison.md"

    written_path = write_retrieval_comparison_report(
        sample_result(),
        output_path=output_path,
    )

    assert written_path == output_path
    text = output_path.read_text(encoding="utf-8")

    assert text.startswith("# Retrieval Comparison Report")
    assert "| hybrid |" in text


def test_phase4_markdown_from_real_eval_lists_keyword_embedding_and_hybrid() -> None:
    result = load_and_compare_phase4_retrievers(
        questions_path=DEFAULT_RETRIEVAL_QUESTIONS_PATH,
        chunks_path=CHUNKS_PATH,
        top_k=5,
        embedding_dimensions=128,
    )

    markdown = format_retrieval_comparison_markdown(result)

    assert "| keyword |" in markdown
    assert "| embedding |" in markdown
    assert "| hybrid |" in markdown
    assert "This report does not claim semantic retrieval superiority." in markdown


def sample_summaries() -> list[RetrieverComparisonSummary]:
    return [
        {
            "retriever_name": "keyword",
            "total_questions": 8,
            "top_k": 5,
            "hit_rate_at_k": 0.75,
            "mean_reciprocal_rank": 0.5,
            "failed_question_ids": ["RET-002"],
            "latency_seconds": 0.1,
        },
        {
            "retriever_name": "embedding",
            "total_questions": 8,
            "top_k": 5,
            "hit_rate_at_k": 0.875,
            "mean_reciprocal_rank": 0.625,
            "failed_question_ids": ["RET-003"],
            "latency_seconds": 0.2,
        },
        {
            "retriever_name": "hybrid",
            "total_questions": 8,
            "top_k": 5,
            "hit_rate_at_k": 0.875,
            "mean_reciprocal_rank": 0.75,
            "failed_question_ids": [],
            "latency_seconds": 0.3,
        },
    ]


def sample_result() -> RetrievalComparisonResult:
    return {
        "generated_at": "2026-06-09T00:00:00Z",
        "top_k": 5,
        "question_count": 8,
        "summaries": sample_summaries(),
    }