from pathlib import Path

from app.retrieval_compare import (
    build_keyword_and_embedding_retrievers,
    compare_retrievers,
    format_retrieval_comparison_markdown,
    load_and_compare_keyword_and_embedding_baselines,
)
from app.retrieval_evaluate import (
    DEFAULT_RETRIEVAL_QUESTIONS_PATH,
    RetrievalQuestion,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "index" / "chunks.jsonl"


def test_build_keyword_and_embedding_retrievers_returns_both_retrievers() -> None:
    retrievers = build_keyword_and_embedding_retrievers(
        chunks_path=CHUNKS_PATH,
        embedding_dimensions=128,
    )

    assert list(retrievers.keys()) == ["keyword", "embedding"]
    assert hasattr(retrievers["keyword"], "search")
    assert hasattr(retrievers["embedding"], "search")


def test_keyword_and_embedding_retrievers_can_run_through_same_comparison_path() -> None:
    retrievers = build_keyword_and_embedding_retrievers(
        chunks_path=CHUNKS_PATH,
        embedding_dimensions=128,
    )
    questions: list[RetrievalQuestion] = [
        {
            "question_id": "RET-LOCAL",
            "query": "flavor refusal oral liquid palatability",
            "expected_source_ids": ["SOP-001", "SOP-004", "SOP-006"],
        }
    ]

    result = compare_retrievers(
        questions=questions,
        retrievers=retrievers,
        top_k=5,
    )

    assert result["question_count"] == 1
    assert [summary["retriever_name"] for summary in result["summaries"]] == [
        "keyword",
        "embedding",
    ]
    assert all(0 <= summary["hit_rate_at_k"] <= 1 for summary in result["summaries"])
    assert all(
        0 <= summary["mean_reciprocal_rank"] <= 1
        for summary in result["summaries"]
    )


def test_keyword_and_embedding_comparison_markdown_lists_both_retrievers() -> None:
    result = load_and_compare_keyword_and_embedding_baselines(
        questions_path=DEFAULT_RETRIEVAL_QUESTIONS_PATH,
        chunks_path=CHUNKS_PATH,
        top_k=5,
        embedding_dimensions=128,
    )

    markdown = format_retrieval_comparison_markdown(result)

    assert "| keyword |" in markdown
    assert "| embedding |" in markdown
    assert "This report does not claim semantic retrieval superiority." in markdown


def test_load_and_compare_keyword_and_embedding_baselines_runs_end_to_end() -> None:
    result = load_and_compare_keyword_and_embedding_baselines(
        questions_path=DEFAULT_RETRIEVAL_QUESTIONS_PATH,
        chunks_path=CHUNKS_PATH,
        top_k=5,
        embedding_dimensions=128,
    )

    keyword_summary = result["summaries"][0]
    embedding_summary = result["summaries"][1]

    assert keyword_summary["retriever_name"] == "keyword"
    assert embedding_summary["retriever_name"] == "embedding"

    assert 0 <= keyword_summary["hit_rate_at_k"] <= 1
    assert 0 <= embedding_summary["hit_rate_at_k"] <= 1
    assert 0 <= keyword_summary["mean_reciprocal_rank"] <= 1
    assert 0 <= embedding_summary["mean_reciprocal_rank"] <= 1


def test_embedding_dimensions_can_change_comparison_result_shape() -> None:
    result = load_and_compare_keyword_and_embedding_baselines(
        questions_path=DEFAULT_RETRIEVAL_QUESTIONS_PATH,
        chunks_path=CHUNKS_PATH,
        top_k=3,
        embedding_dimensions=32,
    )

    embedding_summary = result["summaries"][1]

    assert embedding_summary["retriever_name"] == "embedding"
    assert embedding_summary["top_k"] == 3