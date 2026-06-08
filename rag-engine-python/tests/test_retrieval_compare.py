from pathlib import Path

import pytest



from app.retrieval import ChunkRecord, SearchResult
from app.retrieval_compare import (
    RetrieverComparisonSummary,
    RetrievalComparisonResult,
    build_keyword_baseline_retrievers,
    compare_retrievers,
    comparison_result_to_json,
    format_failed_ids,
    format_retrieval_comparison_markdown,
    load_and_compare_keyword_baseline,
    summarize_evaluation,
    utc_timestamp,
    write_retrieval_comparison_report,
)
from app.retrieval_evaluate import (
    DEFAULT_RETRIEVAL_QUESTIONS_PATH,
    RetrievalEvaluationResult,
    RetrievalQuestion,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "index" / "chunks.jsonl"


class StubRetriever:
    def __init__(self, results: list[SearchResult]) -> None:
        self.calls: list[dict[str, object]] = []
        self._results = results

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        source_type: str | None = None,
    ) -> list[SearchResult]:
        self.calls.append(
            {
                "query": query,
                "top_k": top_k,
                "source_type": source_type,
            }
        )
        return self._results[:top_k]


def test_build_keyword_baseline_retrievers_returns_keyword_retriever() -> None:
    retrievers = build_keyword_baseline_retrievers(chunks_path=CHUNKS_PATH)

    assert list(retrievers.keys()) == ["keyword"]
    assert hasattr(retrievers["keyword"], "search")


def test_compare_retrievers_returns_summary_for_each_retriever() -> None:
    questions: list[RetrievalQuestion] = [
        {
            "question_id": "RET-001",
            "query": "query one",
            "expected_source_ids": ["SOP-001"],
        }
    ]
    retrievers = {
        "keyword": StubRetriever([search_result("SOP-001", score=3.0)]),
        "alternate": StubRetriever([search_result("SOP-999", score=1.0)]),
    }

    result = compare_retrievers(
        questions=questions,
        retrievers=retrievers,
        top_k=5,
    )

    assert result["top_k"] == 5
    assert result["question_count"] == 1
    assert [summary["retriever_name"] for summary in result["summaries"]] == [
        "keyword",
        "alternate",
    ]
    assert result["summaries"][0]["hit_rate_at_k"] == 1.0
    assert result["summaries"][1]["hit_rate_at_k"] == 0.0


def test_compare_retrievers_passes_source_type_to_retriever() -> None:
    question: RetrievalQuestion = {
        "question_id": "RET-001",
        "query": "query one",
        "expected_source_ids": ["SOP-001"],
    }
    retriever = StubRetriever([search_result("SOP-001", score=3.0)])

    compare_retrievers(
        questions=[question],
        retrievers={"keyword": retriever},
        top_k=3,
    )

    assert retriever.calls == [
        {
            "query": "query one",
            "top_k": 3,
            "source_type": "sop",
        }
    ]


def test_compare_retrievers_calculates_summary_metrics() -> None:
    question: RetrievalQuestion = {
        "question_id": "RET-001",
        "query": "query one",
        "expected_source_ids": ["SOP-003"],
    }
    retriever = StubRetriever(
        [
            search_result("SOP-001", score=3.0),
            search_result("SOP-002", score=2.0),
            search_result("SOP-003", score=1.0),
        ]
    )

    result = compare_retrievers(
        questions=[question],
        retrievers={"keyword": retriever},
        top_k=2,
    )

    summary = result["summaries"][0]

    assert summary["hit_rate_at_k"] == 0.0
    assert summary["mean_reciprocal_rank"] == 0.0


def test_compare_retrievers_handles_multiple_expected_sources() -> None:
    question: RetrievalQuestion = {
        "question_id": "RET-001",
        "query": "query one",
        "expected_source_ids": ["SOP-002", "SOP-003"],
    }
    retriever = StubRetriever(
        [
            search_result("SOP-003", score=3.0),
            search_result("SOP-002", score=2.0),
        ]
    )

    result = compare_retrievers(
        questions=[question],
        retrievers={"keyword": retriever},
        top_k=5,
    )

    summary = result["summaries"][0]

    assert summary["hit_rate_at_k"] == 1.0
    assert summary["mean_reciprocal_rank"] == 1.0


def test_compare_retrievers_rejects_empty_questions() -> None:
    with pytest.raises(ValueError, match="at least one retrieval question"):
        compare_retrievers(
            questions=[],
            retrievers={"keyword": StubRetriever([])},
        )


def test_compare_retrievers_rejects_empty_retrievers() -> None:
    question: RetrievalQuestion = {
        "question_id": "RET-001",
        "query": "query one",
        "expected_source_ids": ["SOP-001"],
    }

    with pytest.raises(ValueError, match="at least one retriever"):
        compare_retrievers(
            questions=[question],
            retrievers={},
        )


def test_compare_retrievers_rejects_invalid_top_k() -> None:
    question: RetrievalQuestion = {
        "question_id": "RET-001",
        "query": "query one",
        "expected_source_ids": ["SOP-001"],
    }

    with pytest.raises(ValueError, match="top_k"):
        compare_retrievers(
            questions=[question],
            retrievers={"keyword": StubRetriever([])},
            top_k=0,
        )


def test_summarize_evaluation_copies_evaluation_fields() -> None:
    evaluation: RetrievalEvaluationResult = {
        "total_questions": 2,
        "top_k": 5,
        "hit_rate_at_k": 0.5,
        "mean_reciprocal_rank": 0.25,
        "failed_question_ids": ["RET-002"],
        "question_results": [],
    }

    summary = summarize_evaluation(
        retriever_name="keyword",
        evaluation=evaluation,
        latency_seconds=0.123,
    )

    assert summary == {
        "retriever_name": "keyword",
        "total_questions": 2,
        "top_k": 5,
        "hit_rate_at_k": 0.5,
        "mean_reciprocal_rank": 0.25,
        "failed_question_ids": ["RET-002"],
        "latency_seconds": 0.123,
    }


def test_format_failed_ids_handles_empty_list() -> None:
    assert format_failed_ids([]) == "None"


def test_format_failed_ids_joins_values() -> None:
    assert format_failed_ids(["RET-001", "RET-002"]) == "RET-001, RET-002"


def test_format_retrieval_comparison_markdown_includes_summary_table() -> None:
    result = sample_comparison_result()

    markdown = format_retrieval_comparison_markdown(result)

    assert "# Retrieval Comparison Report" in markdown
    assert "| Retriever | Hit Rate | MRR | Failed IDs | Latency Seconds |" in markdown
    assert "| keyword | 1.000 | 0.500 | RET-002 | 0.123456 |" in markdown
    assert "Keyword retrieval remains the transparent baseline." in markdown


def test_write_retrieval_comparison_report_writes_markdown(tmp_path: Path) -> None:
    output_path = tmp_path / "retrieval_comparison.md"

    written_path = write_retrieval_comparison_report(
        sample_comparison_result(),
        output_path=output_path,
    )

    assert written_path == output_path
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").startswith(
        "# Retrieval Comparison Report"
    )


def test_comparison_result_to_json_returns_readable_json() -> None:
    output = comparison_result_to_json(sample_comparison_result())

    assert '"retriever_name": "keyword"' in output
    assert "\n" in output


def test_utc_timestamp_uses_z_suffix() -> None:
    assert utc_timestamp().endswith("Z")


def test_load_and_compare_keyword_baseline_runs_end_to_end() -> None:
    result = load_and_compare_keyword_baseline(
        questions_path=DEFAULT_RETRIEVAL_QUESTIONS_PATH,
        chunks_path=CHUNKS_PATH,
        top_k=5,
    )

    assert result["question_count"] > 0
    assert result["top_k"] == 5
    assert result["summaries"]
    assert result["summaries"][0]["retriever_name"] == "keyword"
    assert 0 <= result["summaries"][0]["hit_rate_at_k"] <= 1
    assert 0 <= result["summaries"][0]["mean_reciprocal_rank"] <= 1


def sample_comparison_result() -> RetrievalComparisonResult:
    summary: RetrieverComparisonSummary = {
        "retriever_name": "keyword",
        "total_questions": 2,
        "top_k": 5,
        "hit_rate_at_k": 1.0,
        "mean_reciprocal_rank": 0.5,
        "failed_question_ids": ["RET-002"],
        "latency_seconds": 0.123456,
    }

    return {
        "generated_at": "2026-06-08T00:00:00Z",
        "top_k": 5,
        "question_count": 2,
        "summaries": [summary],
    }


def search_result(source_id: str, *, score: float) -> SearchResult:
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