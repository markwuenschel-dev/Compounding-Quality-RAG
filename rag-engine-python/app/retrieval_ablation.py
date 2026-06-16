from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict

from pydantic import ValidationError

from app.holdout_evaluate import (
    RetrievalHoldoutEvaluationResult,
    RetrievalHoldoutQuestion,
    evaluate_retrieval_holdout,
    load_retrieval_holdout_questions,
)
from app.llm_client import (
    LLMClientError,
    OpenAIJsonClient,
    openai_json_client_from_env,
)
from app.retrieval import (
    DEFAULT_CHUNKS_PATH,
    KeywordRetriever,
    Retriever,
    load_chunks,
)
from app.retrieval_query_strategy import (
    DeterministicExpansionStrategy,
    NanoStructuredQueryStrategy,
    RawQueryStrategy,
    RetrievalIntentCache,
    RetrievalQueryIntent,
    RetrievalQueryStrategy,
    StrategyName,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACTS_ROOT = PROJECT_ROOT / "artifacts" / "runs"
DEFAULT_RUN_ID = "retrieval-dev-ablation"
DEFAULT_STRATEGIES = (
    "raw",
    "deterministic_expansion",
    "nano_structured",
)
ALLOWED_STRATEGIES = set(DEFAULT_STRATEGIES)


class StrategyQuestionResult(TypedDict):
    question_id: str
    original_query: str
    search_text: str
    issue_tags: list[str]
    required_topics: list[str]
    excluded_topics: list[str]
    expected_source_ids: list[str]
    forbidden_source_ids: list[str]
    retrieved_source_ids: list[str]
    hit: bool
    reciprocal_rank: float
    forbidden_source_hits: list[str]
    negative_constraints_passed: bool
    used_fallback: bool


class StrategyEvaluationSummary(TypedDict):
    strategy: str
    total_questions: int
    top_k: int
    hit_rate_at_k: float
    mean_reciprocal_rank: float
    negative_constraint_pass_rate: float
    failed_question_ids: list[str]
    forbidden_hit_question_ids: list[str]
    query_build_latency_seconds: float
    retrieval_latency_seconds: float
    total_latency_seconds: float
    model_call_count: int
    cache_hit_count: int
    cache_miss_count: int
    fallback_count: int
    structured_output_failure_count: int
    model_error_count: int


class StrategyEvaluationResult(TypedDict):
    summary: StrategyEvaluationSummary
    question_results: list[StrategyQuestionResult]


class RetrievalAblationResult(TypedDict):
    generated_at: str
    run_id: str
    question_count: int
    top_k: int
    question_file: str
    chunks_file: str
    nano_model: str | None
    strategies: list[str]
    summaries: list[StrategyEvaluationSummary]
    artifacts_directory: str


class NanoBuildStats:
    def __init__(self) -> None:
        self.model_call_count = 0
        self.cache_hit_count = 0
        self.cache_miss_count = 0
        self.fallback_count = 0
        self.structured_output_failure_count = 0
        self.model_error_count = 0


class NanoIntentBuilder:
    def __init__(
        self,
        *,
        client: OpenAIJsonClient,
        cache: RetrievalIntentCache,
        model_name: str,
        fallback_strategy: RetrievalQueryStrategy,
        refresh_cache: bool,
    ) -> None:
        self._strategy = NanoStructuredQueryStrategy(client)
        self._cache = cache
        self._model_name = model_name
        self._fallback_strategy = fallback_strategy
        self._refresh_cache = refresh_cache
        self.stats = NanoBuildStats()

    def build(
        self,
        *,
        question_id: str,
        concern_text: str,
    ) -> tuple[RetrievalQueryIntent, bool]:
        if not self._refresh_cache:
            cached = self._cache.get(
                question_id=question_id,
                concern_text=concern_text,
                model=self._model_name,
            )
            if cached is not None:
                self.stats.cache_hit_count += 1
                return cached, False

        self.stats.cache_miss_count += 1
        self.stats.model_call_count += 1

        try:
            intent = self._strategy.build(concern_text)
        except LLMClientError:
            self.stats.model_error_count += 1
            raise
        except (
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
            ValidationError,
        ):
            self.stats.structured_output_failure_count += 1
            self.stats.fallback_count += 1
            return self._fallback_strategy.build(concern_text), True

        self._cache.put(
            question_id=question_id,
            concern_text=concern_text,
            model=self._model_name,
            intent=intent,
        )
        return intent, False

    def flush(self) -> None:
        self._cache.flush()


def parse_strategy_names(value: str | list[str]) -> list[StrategyName]:
    raw_values = (
        value.split(",")
        if isinstance(value, str)
        else value
    )
    names: list[StrategyName] = []
    seen: set[str] = set()

    for raw_name in raw_values:
        name = raw_name.strip()
        if not name:
            continue
        if name not in ALLOWED_STRATEGIES:
            raise ValueError(
                f"Unknown retrieval query strategy: {name}. "
                f"Allowed values: {sorted(ALLOWED_STRATEGIES)}"
            )
        if name in seen:
            continue
        seen.add(name)
        names.append(name)  # type: ignore[arg-type]

    if not names:
        raise ValueError("At least one retrieval query strategy is required")

    return names


def run_retrieval_ablation(
    *,
    questions_path: Path,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    top_k: int = 5,
    strategy_names: list[StrategyName] | None = None,
    run_id: str = DEFAULT_RUN_ID,
    artifacts_root: Path = DEFAULT_ARTIFACTS_ROOT,
    nano_model: str | None = None,
    refresh_nano: bool = False,
    retriever: Retriever | None = None,
    nano_client: OpenAIJsonClient | None = None,
) -> RetrievalAblationResult:
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    clean_run_id = normalize_run_id(run_id)
    active_strategies = strategy_names or list(DEFAULT_STRATEGIES)
    questions = load_retrieval_holdout_questions(questions_path)
    active_retriever = retriever or KeywordRetriever(
        load_chunks(chunks_path)
    )
    run_directory = artifacts_root / clean_run_id
    run_directory.mkdir(parents=True, exist_ok=True)
    nano_cache_path = run_directory / "nano_intents.jsonl"

    active_nano_client: OpenAIJsonClient | None = None
    active_nano_model: str | None = None

    if "nano_structured" in active_strategies:
        active_nano_client = nano_client or build_nano_client(
            nano_model
        )
        active_nano_model = active_nano_client.model

    strategy_results: list[StrategyEvaluationResult] = []

    for strategy_name in active_strategies:
        result = evaluate_query_strategy(
            strategy_name=strategy_name,
            questions=questions,
            retriever=active_retriever,
            top_k=top_k,
            nano_client=active_nano_client,
            nano_model=active_nano_model,
            nano_cache_path=nano_cache_path,
            refresh_nano=refresh_nano,
        )
        strategy_results.append(result)
        write_json(
            run_directory / f"{strategy_name}_results.json",
            result,
        )

    comparison: RetrievalAblationResult = {
        "generated_at": utc_timestamp(),
        "run_id": clean_run_id,
        "question_count": len(questions),
        "top_k": top_k,
        "question_file": display_path(questions_path),
        "chunks_file": display_path(chunks_path),
        "nano_model": active_nano_model,
        "strategies": list(active_strategies),
        "summaries": [
            result["summary"]
            for result in strategy_results
        ],
        "artifacts_directory": display_path(run_directory),
    }

    write_json(
        run_directory / "comparison.json",
        comparison,
    )
    (run_directory / "comparison.md").write_text(
        format_comparison_markdown(
            comparison,
            strategy_results,
        ),
        encoding="utf-8",
    )
    write_json(
        run_directory / "run_manifest.json",
        {
            "generated_at": comparison["generated_at"],
            "run_id": clean_run_id,
            "question_file": display_path(questions_path),
            "question_file_sha256": sha256_file(questions_path),
            "chunks_file": display_path(chunks_path),
            "chunks_file_sha256": sha256_file(chunks_path),
            "top_k": top_k,
            "strategies": list(active_strategies),
            "nano_model": active_nano_model,
        },
    )

    return comparison


def evaluate_query_strategy(
    *,
    strategy_name: StrategyName,
    questions: list[RetrievalHoldoutQuestion],
    retriever: Retriever,
    top_k: int,
    nano_client: OpenAIJsonClient | None,
    nano_model: str | None,
    nano_cache_path: Path,
    refresh_nano: bool,
) -> StrategyEvaluationResult:
    query_build_start = time.perf_counter()
    intents: dict[str, RetrievalQueryIntent] = {}
    fallback_by_question: dict[str, bool] = {}
    nano_stats = NanoBuildStats()

    if strategy_name == "raw":
        strategy: RetrievalQueryStrategy = RawQueryStrategy()
        for question in questions:
            intents[question["question_id"]] = strategy.build(
                question["query"]
            )
            fallback_by_question[question["question_id"]] = False
    elif strategy_name == "deterministic_expansion":
        strategy = DeterministicExpansionStrategy()
        for question in questions:
            intents[question["question_id"]] = strategy.build(
                question["query"]
            )
            fallback_by_question[question["question_id"]] = False
    else:
        if nano_client is None or nano_model is None:
            raise ValueError(
                "nano_structured requires an OpenAI JSON client"
            )

        builder = NanoIntentBuilder(
            client=nano_client,
            cache=RetrievalIntentCache(nano_cache_path),
            model_name=nano_model,
            fallback_strategy=DeterministicExpansionStrategy(),
            refresh_cache=refresh_nano,
        )

        for question in questions:
            intent, used_fallback = builder.build(
                question_id=question["question_id"],
                concern_text=question["query"],
            )
            intents[question["question_id"]] = intent
            fallback_by_question[question["question_id"]] = (
                used_fallback
            )

        builder.flush()
        nano_stats = builder.stats

    query_build_latency = time.perf_counter() - query_build_start
    transformed_questions = [
        transform_question(
            question,
            intents[question["question_id"]],
        )
        for question in questions
    ]

    retrieval_start = time.perf_counter()
    evaluation = evaluate_retrieval_holdout(
        transformed_questions,
        top_k=top_k,
        retriever=retriever,
    )
    retrieval_latency = time.perf_counter() - retrieval_start

    question_results = enrich_question_results(
        original_questions=questions,
        evaluation=evaluation,
        intents=intents,
        fallback_by_question=fallback_by_question,
    )

    summary: StrategyEvaluationSummary = {
        "strategy": strategy_name,
        "total_questions": evaluation["total_questions"],
        "top_k": evaluation["top_k"],
        "hit_rate_at_k": evaluation["hit_rate_at_k"],
        "mean_reciprocal_rank": evaluation[
            "mean_reciprocal_rank"
        ],
        "negative_constraint_pass_rate": evaluation[
            "negative_constraint_pass_rate"
        ],
        "failed_question_ids": list(
            evaluation["failed_question_ids"]
        ),
        "forbidden_hit_question_ids": list(
            evaluation["forbidden_hit_question_ids"]
        ),
        "query_build_latency_seconds": query_build_latency,
        "retrieval_latency_seconds": retrieval_latency,
        "total_latency_seconds": (
            query_build_latency + retrieval_latency
        ),
        "model_call_count": nano_stats.model_call_count,
        "cache_hit_count": nano_stats.cache_hit_count,
        "cache_miss_count": nano_stats.cache_miss_count,
        "fallback_count": nano_stats.fallback_count,
        "structured_output_failure_count": (
            nano_stats.structured_output_failure_count
        ),
        "model_error_count": nano_stats.model_error_count,
    }

    return {
        "summary": summary,
        "question_results": question_results,
    }


def transform_question(
    question: RetrievalHoldoutQuestion,
    intent: RetrievalQueryIntent,
) -> RetrievalHoldoutQuestion:
    transformed: RetrievalHoldoutQuestion = {
        "question_id": question["question_id"],
        "query": intent.search_text,
        "expected_source_ids": list(
            question["expected_source_ids"]
        ),
        "forbidden_source_ids": list(
            question.get("forbidden_source_ids", [])
        ),
    }

    if "rationale" in question:
        transformed["rationale"] = question["rationale"]

    return transformed


def enrich_question_results(
    *,
    original_questions: list[RetrievalHoldoutQuestion],
    evaluation: RetrievalHoldoutEvaluationResult,
    intents: dict[str, RetrievalQueryIntent],
    fallback_by_question: dict[str, bool],
) -> list[StrategyQuestionResult]:
    questions_by_id = {
        question["question_id"]: question
        for question in original_questions
    }

    return [
        {
            "question_id": result["question_id"],
            "original_query": questions_by_id[
                result["question_id"]
            ]["query"],
            "search_text": intents[
                result["question_id"]
            ].search_text,
            "issue_tags": list(
                intents[result["question_id"]].issue_tags
            ),
            "required_topics": list(
                intents[result["question_id"]].required_topics
            ),
            "excluded_topics": list(
                intents[result["question_id"]].excluded_topics
            ),
            "expected_source_ids": list(
                result["expected_source_ids"]
            ),
            "forbidden_source_ids": list(
                result["forbidden_source_ids"]
            ),
            "retrieved_source_ids": list(
                result["retrieved_source_ids"]
            ),
            "hit": result["hit"],
            "reciprocal_rank": result["reciprocal_rank"],
            "forbidden_source_hits": list(
                result["forbidden_source_hits"]
            ),
            "negative_constraints_passed": result[
                "negative_constraints_passed"
            ],
            "used_fallback": fallback_by_question[
                result["question_id"]
            ],
        }
        for result in evaluation["question_results"]
    ]


def build_nano_client(
    model_name: str | None,
) -> OpenAIJsonClient:
    if model_name is None:
        return openai_json_client_from_env()

    return OpenAIJsonClient(model=model_name)


def format_comparison_markdown(
    comparison: RetrievalAblationResult,
    strategy_results: list[StrategyEvaluationResult],
) -> str:
    lines = [
        "# Retrieval Query Ablation",
        "",
        f"Generated: `{comparison['generated_at']}`",
        f"Run ID: `{comparison['run_id']}`",
        f"Question count: `{comparison['question_count']}`",
        f"Top K: `{comparison['top_k']}`",
        f"Nano model: `{comparison['nano_model'] or 'not used'}`",
        "",
        "## Summary",
        "",
        (
            "| Strategy | Hit Rate@K | MRR | Negative Pass Rate | "
            "Failed | Forbidden Hits | Total Seconds | "
            "Model Calls | Cache Hits | Fallbacks |"
        ),
        (
            "|---|---:|---:|---:|---:|---:|---:|"
            "---:|---:|---:|"
        ),
    ]

    for summary in comparison["summaries"]:
        lines.append(
            "| "
            f"{summary['strategy']} | "
            f"{summary['hit_rate_at_k']:.3f} | "
            f"{summary['mean_reciprocal_rank']:.3f} | "
            f"{summary['negative_constraint_pass_rate']:.3f} | "
            f"{len(summary['failed_question_ids'])} | "
            f"{len(summary['forbidden_hit_question_ids'])} | "
            f"{summary['total_latency_seconds']:.3f} | "
            f"{summary['model_call_count']} | "
            f"{summary['cache_hit_count']} | "
            f"{summary['fallback_count']} |"
        )

    lines.extend(
        [
            "",
            "## Question-Level Changes",
            "",
        ]
    )

    by_strategy = {
        result["summary"]["strategy"]: {
            question["question_id"]: question
            for question in result["question_results"]
        }
        for result in strategy_results
    }
    question_ids = [
        question["question_id"]
        for question in strategy_results[0]["question_results"]
    ]

    lines.extend(
        [
            "| Question | "
            + " | ".join(comparison["strategies"])
            + " |",
            "|---|"
            + "|".join("---" for _ in comparison["strategies"])
            + "|",
        ]
    )

    for question_id in question_ids:
        cells = []

        for strategy_name in comparison["strategies"]:
            result = by_strategy[strategy_name][question_id]
            status = (
                f"hit@{format_rank(result['reciprocal_rank'])}"
                if result["hit"]
                else "miss"
            )
            if not result["negative_constraints_passed"]:
                status += " + forbidden"
            if result["used_fallback"]:
                status += " + fallback"
            cells.append(status)

        lines.append(
            f"| {question_id} | "
            + " | ".join(cells)
            + " |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The retriever, corpus, chunks, top-K, labels, and scoring are held constant.",
            "- Only the query-building strategy changes.",
            "- A nano fallback means the structured output was unusable and deterministic expansion was used.",
            "- Cache hits replay the exact previously validated nano intent.",
            "- This development comparison should not be used to tune the frozen holdout.",
            "",
        ]
    )

    return "\n".join(lines)


def format_rank(reciprocal_rank: float) -> str:
    if reciprocal_rank <= 0:
        return "-"
    return str(round(1 / reciprocal_rank))


def normalize_run_id(value: str) -> str:
    clean = value.strip()
    if not clean:
        raise ValueError("run_id must not be blank")
    if any(
        character not in "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        for character in clean
    ):
        raise ValueError(
            "run_id may contain only letters, numbers, hyphens, and underscores"
        )
    return clean


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(
            path.resolve().relative_to(
                PROJECT_ROOT.resolve()
            )
        )
    except ValueError:
        return str(path.resolve())


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
