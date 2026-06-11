from __future__ import annotations

from collections.abc import Mapping
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, TypedDict

from app.retrieval import (
    DEFAULT_CHUNKS_PATH,
    KeywordRetriever,
    Retriever,
    load_chunks,
)
from app.retrieval_embedding import EmbeddingRetriever, HashingEmbeddingModel
from app.retrieval_evaluate import (
    DEFAULT_RETRIEVAL_QUESTIONS_PATH,
    RetrievalEvaluationResult,
    RetrievalQuestion,
    evaluate_retrieval_questions,
    load_retrieval_questions,
)
from app.retrieval_hybrid import HybridRetriever


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMPARISON_REPORT_PATH = (
    PROJECT_ROOT / "reports" / "retrieval_comparison.md"
)


class RetrieverComparisonSummary(TypedDict):
    retriever_name: str
    total_questions: int
    top_k: int
    hit_rate_at_k: float
    mean_reciprocal_rank: float
    failed_question_ids: list[str]
    latency_seconds: float


class RetrievalComparisonResult(TypedDict):
    generated_at: str
    top_k: int
    question_count: int
    summaries: list[RetrieverComparisonSummary]


def build_keyword_baseline_retrievers(
    *,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
) -> dict[str, Retriever]:
    chunks = load_chunks(chunks_path)

    return {
        "keyword": KeywordRetriever(chunks),
    }


def build_keyword_and_embedding_retrievers(
    *,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    embedding_dimensions: int = 128,
) -> dict[str, Retriever]:
    chunks = load_chunks(chunks_path)
    embedding_model = HashingEmbeddingModel(dimensions=embedding_dimensions)

    return {
        "keyword": KeywordRetriever(chunks),
        "embedding": EmbeddingRetriever(
            chunks=chunks,
            embedding_model=embedding_model,
        ),
    }


def build_phase4_retrievers(
    *,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    embedding_dimensions: int = 128,
    hybrid_keyword_weight: float = 0.65,
    hybrid_embedding_weight: float = 0.35,
) -> dict[str, Retriever]:
    chunks = load_chunks(chunks_path)
    embedding_model = HashingEmbeddingModel(dimensions=embedding_dimensions)

    return {
        "keyword": KeywordRetriever(chunks),
        "embedding": EmbeddingRetriever(
            chunks=chunks,
            embedding_model=embedding_model,
        ),
        "hybrid": HybridRetriever(
            chunks=chunks,
            embedding_model=embedding_model,
            keyword_weight=hybrid_keyword_weight,
            embedding_weight=hybrid_embedding_weight,
        ),
    }


def compare_retrievers(
    *,
    questions: list[RetrievalQuestion],
    retrievers: Mapping[str, Retriever],
    top_k: int = 5,
) -> RetrievalComparisonResult:
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if not questions:
        raise ValueError("questions must contain at least one retrieval question")

    if not retrievers:
        raise ValueError("retrievers must contain at least one retriever")

    summaries = [
        evaluate_named_retriever(
            retriever_name=name,
            retriever=retriever,
            questions=questions,
            top_k=top_k,
        )
        for name, retriever in retrievers.items()
    ]

    return {
        "generated_at": utc_timestamp(),
        "top_k": top_k,
        "question_count": len(questions),
        "summaries": summaries,
    }


def evaluate_named_retriever(
    *,
    retriever_name: str,
    retriever: Retriever,
    questions: list[RetrievalQuestion],
    top_k: int,
) -> RetrieverComparisonSummary:
    start_time = time.perf_counter()

    evaluation = evaluate_retrieval_questions(
        questions,
        top_k=top_k,
        retriever=retriever,
    )

    latency_seconds = time.perf_counter() - start_time

    return summarize_evaluation(
        retriever_name=retriever_name,
        evaluation=evaluation,
        latency_seconds=latency_seconds,
    )


def summarize_evaluation(
    *,
    retriever_name: str,
    evaluation: RetrievalEvaluationResult,
    latency_seconds: float,
) -> RetrieverComparisonSummary:
    return {
        "retriever_name": retriever_name,
        "total_questions": evaluation["total_questions"],
        "top_k": evaluation["top_k"],
        "hit_rate_at_k": evaluation["hit_rate_at_k"],
        "mean_reciprocal_rank": evaluation["mean_reciprocal_rank"],
        "failed_question_ids": list(evaluation["failed_question_ids"]),
        "latency_seconds": latency_seconds,
    }


def load_and_compare_keyword_baseline(
    *,
    questions_path: Path = DEFAULT_RETRIEVAL_QUESTIONS_PATH,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    top_k: int = 5,
) -> RetrievalComparisonResult:
    questions = load_retrieval_questions(questions_path)
    retrievers = build_keyword_baseline_retrievers(chunks_path=chunks_path)

    return compare_retrievers(
        questions=questions,
        retrievers=retrievers,
        top_k=top_k,
    )


def load_and_compare_keyword_and_embedding_baselines(
    *,
    questions_path: Path = DEFAULT_RETRIEVAL_QUESTIONS_PATH,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    top_k: int = 5,
    embedding_dimensions: int = 128,
) -> RetrievalComparisonResult:
    questions = load_retrieval_questions(questions_path)
    retrievers = build_keyword_and_embedding_retrievers(
        chunks_path=chunks_path,
        embedding_dimensions=embedding_dimensions,
    )

    return compare_retrievers(
        questions=questions,
        retrievers=retrievers,
        top_k=top_k,
    )


def load_and_compare_phase4_retrievers(
    *,
    questions_path: Path = DEFAULT_RETRIEVAL_QUESTIONS_PATH,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    top_k: int = 5,
    embedding_dimensions: int = 128,
    hybrid_keyword_weight: float = 0.65,
    hybrid_embedding_weight: float = 0.35,
) -> RetrievalComparisonResult:
    questions = load_retrieval_questions(questions_path)
    retrievers = build_phase4_retrievers(
        chunks_path=chunks_path,
        embedding_dimensions=embedding_dimensions,
        hybrid_keyword_weight=hybrid_keyword_weight,
        hybrid_embedding_weight=hybrid_embedding_weight,
    )

    return compare_retrievers(
        questions=questions,
        retrievers=retrievers,
        top_k=top_k,
    )


def format_retrieval_comparison_markdown(
    result: RetrievalComparisonResult,
) -> str:
    lines = [
        "# Retrieval Comparison Report",
        "",
        f"Generated: `{result['generated_at']}`",
        f"Top K: `{result['top_k']}`",
        f"Question count: `{result['question_count']}`",
        "",
        "## Summary",
        "",
        "| Retriever | Hit Rate | MRR | Failed IDs | Latency Seconds |",
        "|---|---:|---:|---|---:|",
    ]

    for summary in result["summaries"]:
        lines.append(
            "| "
            f"{summary['retriever_name']} | "
            f"{summary['hit_rate_at_k']:.3f} | "
            f"{summary['mean_reciprocal_rank']:.3f} | "
            f"{format_failed_ids(summary['failed_question_ids'])} | "
            f"{summary['latency_seconds']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Qualitative Notes",
            "",
            *format_qualitative_notes(result),
            "",
            "## Interpretation Guardrails",
            "",
            "- Keyword retrieval remains the transparent baseline.",
            "- Hashing embeddings are a local deterministic vector baseline, not production semantic search.",
            "- Hybrid retrieval combines normalized keyword and embedding scores; it does not prove quality by itself.",
            "- This report does not claim semantic retrieval superiority.",
            "- Corpus text should not be changed merely to improve retrieval metrics.",
            "",
        ]
    )

    return "\n".join(lines)


def format_qualitative_notes(result: RetrievalComparisonResult) -> list[str]:
    summaries = result["summaries"]

    if not summaries:
        return ["- No retriever summaries were available."]

    best_hit_rate_names = best_retriever_names(
        summaries,
        metric_name="hit_rate_at_k",
    )
    best_mrr_names = best_retriever_names(
        summaries,
        metric_name="mean_reciprocal_rank",
    )

    lines = [
        f"- Best hit_rate@k: {', '.join(best_hit_rate_names)}.",
        f"- Best MRR: {', '.join(best_mrr_names)}.",
    ]

    keyword = find_summary(summaries, "keyword")
    embedding = find_summary(summaries, "embedding")
    hybrid = find_summary(summaries, "hybrid")

    if keyword and embedding:
        keyword_only_failures = sorted(
            set(keyword["failed_question_ids"]) - set(embedding["failed_question_ids"])
        )
        embedding_only_failures = sorted(
            set(embedding["failed_question_ids"]) - set(keyword["failed_question_ids"])
        )

        lines.append(
            "- Keyword failed questions not failed by embedding: "
            f"{format_failed_ids(keyword_only_failures)}."
        )
        lines.append(
            "- Embedding failed questions not failed by keyword: "
            f"{format_failed_ids(embedding_only_failures)}."
        )

    if hybrid and keyword:
        hybrid_new_failures = sorted(
            set(hybrid["failed_question_ids"]) - set(keyword["failed_question_ids"])
        )
        hybrid_resolved_keyword_failures = sorted(
            set(keyword["failed_question_ids"]) - set(hybrid["failed_question_ids"])
        )

        lines.append(
            "- Hybrid failures not present in keyword baseline: "
            f"{format_failed_ids(hybrid_new_failures)}."
        )
        lines.append(
            "- Keyword failures resolved by hybrid: "
            f"{format_failed_ids(hybrid_resolved_keyword_failures)}."
        )

    return lines


MetricName = Literal["hit_rate_at_k", "mean_reciprocal_rank"]


def best_retriever_names(
    summaries: list[RetrieverComparisonSummary],
    *,
    metric_name: MetricName,
) -> list[str]:
    if not summaries:
        return []

    best_value = max(metric_value(summary, metric_name) for summary in summaries)

    return [
        summary["retriever_name"]
        for summary in summaries
        if metric_value(summary, metric_name) == best_value
    ]


def metric_value(
    summary: RetrieverComparisonSummary,
    metric_name: MetricName,
) -> float:
    if metric_name == "hit_rate_at_k":
        return summary["hit_rate_at_k"]

    return summary["mean_reciprocal_rank"]

def find_summary(
    summaries: list[RetrieverComparisonSummary],
    retriever_name: str,
) -> RetrieverComparisonSummary | None:
    for summary in summaries:
        if summary["retriever_name"] == retriever_name:
            return summary

    return None


def write_retrieval_comparison_report(
    result: RetrievalComparisonResult,
    *,
    output_path: Path = DEFAULT_COMPARISON_REPORT_PATH,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        format_retrieval_comparison_markdown(result),
        encoding="utf-8",
    )

    return output_path


def comparison_result_to_json(result: RetrievalComparisonResult) -> str:
    return json.dumps(result, indent=2)


def format_failed_ids(failed_question_ids: list[str]) -> str:
    if not failed_question_ids:
        return "None"

    return ", ".join(failed_question_ids)


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> None:
    result = load_and_compare_phase4_retrievers()
    write_retrieval_comparison_report(result)
    print(comparison_result_to_json(result))


if __name__ == "__main__":
    main()