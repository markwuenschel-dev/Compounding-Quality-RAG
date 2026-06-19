from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, TypedDict, cast

from pydantic import ValidationError

from app.holdout_evaluate import (
    RetrievalHoldoutEvaluationResult,
    RetrievalHoldoutQuestion,
    evaluate_retrieval_holdout,
    load_retrieval_holdout_questions,
)
from app.llm_client import LLMClientError, OpenAIJsonClient, openai_json_client_from_env
from app.retrieval import DEFAULT_CHUNKS_PATH, KeywordRetriever, Retriever, load_chunks
from app.retrieval_intent import (
    INTENT_SCHEMA_VERSION,
    NanoIntentDetector,
    RetrievalIntentTag,
    RuleIntentDetector,
    SemanticIntentTag,
    UnknownIntentTagError,
    unmapped_intent_tags,
)
from app.retrieval_query_strategy import (
    BuiltRetrievalQuery,
    DeterministicExpansionStrategy,
    RawQueryStrategy,
    RetrievalIntentCache,
    RetrievalQueryStrategy,
    RuleIntentQueryStrategy,
    StrategyName,
    build_query_from_semantic_intent,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACTS_ROOT = PROJECT_ROOT / "artifacts" / "runs"
DEFAULT_RUN_ID = "retrieval-intent-ablation"
DEFAULT_STRATEGIES: tuple[StrategyName, ...] = (
    "raw",
    "deterministic_expansion",
    "rule_intent",
    "nano_intent",
)
ALLOWED_STRATEGIES = set(DEFAULT_STRATEGIES)


class IntentMetric(TypedDict):
    precision: float
    recall: float
    true_positive: int
    predicted: int
    expected: int


class StrategyQuestionResult(TypedDict):
    question_id: str
    original_query: str
    search_text: str
    predicted_semantic_intent_tags: list[str]
    expected_semantic_intent_tags: list[str]
    semantic_intent_exact_match: bool | None
    predicted_intent_tags: list[str]
    expected_intent_tags: list[str]
    intent_exact_match: bool | None
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
    unknown_tag_count: int
    unmapped_tag_count: int
    semantic_intent_micro_precision: float | None
    semantic_intent_micro_recall: float | None
    semantic_intent_exact_match_rate: float | None
    per_semantic_tag_metrics: dict[str, IntentMetric]
    intent_micro_precision: float | None
    intent_micro_recall: float | None
    intent_exact_match_rate: float | None
    per_tag_metrics: dict[str, IntentMetric]


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
    intent_schema_version: str
    strategies: list[str]
    summaries: list[StrategyEvaluationSummary]
    artifacts_directory: str


class NamedJsonCompletionClient(Protocol):
    @property
    def model(self) -> str:
        ...

    def complete_json(self, prompt: str) -> str:
        ...


class NanoBuildStats:
    def __init__(self) -> None:
        self.model_call_count = 0
        self.cache_hit_count = 0
        self.cache_miss_count = 0
        self.fallback_count = 0
        self.structured_output_failure_count = 0
        self.model_error_count = 0
        self.unknown_tag_count = 0


class NanoIntentBuilder:
    def __init__(
        self,
        *,
        client: NamedJsonCompletionClient,
        cache: RetrievalIntentCache,
        model_name: str,
        refresh_cache: bool,
    ) -> None:
        self._detector = NanoIntentDetector(client)
        self._rule_detector = RuleIntentDetector()
        self._cache = cache
        self._model_name = model_name
        self._refresh_cache = refresh_cache
        self.stats = NanoBuildStats()

    def build(
        self,
        *,
        question_id: str,
        concern_text: str,
    ) -> tuple[BuiltRetrievalQuery, bool]:
        if not self._refresh_cache:
            cached = self._cache.get(
                question_id=question_id,
                concern_text=concern_text,
                model=self._model_name,
                intent_schema_version=INTENT_SCHEMA_VERSION,
            )
            if cached is not None:
                self.stats.cache_hit_count += 1
                return build_query_from_semantic_intent(
                    concern_text,
                    cached,
                    strategy="nano_intent",
                ), False

        self.stats.cache_miss_count += 1
        self.stats.model_call_count += 1

        try:
            intent = self._detector.detect(concern_text)
        except UnknownIntentTagError as exc:
            self.stats.unknown_tag_count += len(exc.unknown_tags)
            self.stats.structured_output_failure_count += 1
            return self._fallback(concern_text), True
        except LLMClientError:
            self.stats.model_error_count += 1
            return self._fallback(concern_text), True
        except (
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
            ValidationError,
        ):
            self.stats.structured_output_failure_count += 1
            return self._fallback(concern_text), True

        self._cache.put(
            question_id=question_id,
            concern_text=concern_text,
            model=self._model_name,
            semantic_intent=intent,
            intent_schema_version=INTENT_SCHEMA_VERSION,
        )
        return build_query_from_semantic_intent(
            concern_text,
            intent,
            strategy="nano_intent",
        ), False

    def _fallback(self, concern_text: str) -> BuiltRetrievalQuery:
        self.stats.fallback_count += 1
        semantic_intent = self._rule_detector.detect(concern_text)
        return build_query_from_semantic_intent(
            concern_text,
            semantic_intent,
            strategy="nano_intent",
        )

    def flush(self) -> None:
        self._cache.flush()


def parse_strategy_names(value: str | list[str]) -> list[StrategyName]:
    raw_values = value.split(",") if isinstance(value, str) else value
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
        names.append(cast(StrategyName, name))
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
    nano_client: NamedJsonCompletionClient | None = None,
) -> RetrievalAblationResult:
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    clean_run_id = normalize_run_id(run_id)
    active_strategies = strategy_names or list(DEFAULT_STRATEGIES)
    questions = load_retrieval_holdout_questions(questions_path)
    active_retriever = retriever or KeywordRetriever(load_chunks(chunks_path))
    run_directory = artifacts_root / clean_run_id
    run_directory.mkdir(parents=True, exist_ok=True)
    nano_cache_path = run_directory / "nano_intents.jsonl"

    active_nano_client: NamedJsonCompletionClient | None = None
    active_nano_model: str | None = None
    if "nano_intent" in active_strategies:
        active_nano_client = nano_client or build_nano_client(nano_model)
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
        write_json(run_directory / f"{strategy_name}_results.json", result)

    comparison: RetrievalAblationResult = {
        "generated_at": utc_timestamp(),
        "run_id": clean_run_id,
        "question_count": len(questions),
        "top_k": top_k,
        "question_file": display_path(questions_path),
        "chunks_file": display_path(chunks_path),
        "nano_model": active_nano_model,
        "intent_schema_version": INTENT_SCHEMA_VERSION,
        "strategies": list(active_strategies),
        "summaries": [result["summary"] for result in strategy_results],
        "artifacts_directory": display_path(run_directory),
    }
    write_json(run_directory / "comparison.json", comparison)
    (run_directory / "comparison.md").write_text(
        format_comparison_markdown(comparison, strategy_results),
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
            "intent_schema_version": INTENT_SCHEMA_VERSION,
        },
    )
    return comparison


def evaluate_query_strategy(
    *,
    strategy_name: StrategyName,
    questions: list[RetrievalHoldoutQuestion],
    retriever: Retriever,
    top_k: int,
    nano_client: NamedJsonCompletionClient | None,
    nano_model: str | None,
    nano_cache_path: Path,
    refresh_nano: bool,
) -> StrategyEvaluationResult:
    query_build_start = time.perf_counter()
    built_queries: dict[str, BuiltRetrievalQuery] = {}
    fallback_by_question: dict[str, bool] = {}
    nano_stats = NanoBuildStats()

    strategy: RetrievalQueryStrategy

    if strategy_name == "raw":
        strategy = RawQueryStrategy()
        for question in questions:
            built_queries[question["question_id"]] = strategy.build(question["query"])
            fallback_by_question[question["question_id"]] = False
    elif strategy_name == "deterministic_expansion":
        strategy = DeterministicExpansionStrategy()
        for question in questions:
            built_queries[question["question_id"]] = strategy.build(question["query"])
            fallback_by_question[question["question_id"]] = False
    elif strategy_name == "rule_intent":
        strategy = RuleIntentQueryStrategy()
        for question in questions:
            built_queries[question["question_id"]] = strategy.build(question["query"])
            fallback_by_question[question["question_id"]] = False
    else:
        if nano_client is None or nano_model is None:
            raise ValueError("nano_intent requires an OpenAI JSON client")
        builder = NanoIntentBuilder(
            client=nano_client,
            cache=RetrievalIntentCache(nano_cache_path),
            model_name=nano_model,
            refresh_cache=refresh_nano,
        )
        for question in questions:
            built, used_fallback = builder.build(
                question_id=question["question_id"],
                concern_text=question["query"],
            )
            built_queries[question["question_id"]] = built
            fallback_by_question[question["question_id"]] = used_fallback
        builder.flush()
        nano_stats = builder.stats

    query_build_latency = time.perf_counter() - query_build_start
    transformed_questions = [
        transform_question(
            question,
            built_queries[question["question_id"]],
            strategy_name=strategy_name,
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
        built_queries=built_queries,
        fallback_by_question=fallback_by_question,
    )
    semantic_intent_metrics = calculate_semantic_intent_metrics(
        question_results
    )
    intent_metrics = calculate_intent_metrics(question_results)
    unmapped_count = sum(
        len(unmapped_intent_tags(query.intent))
        for query in built_queries.values()
        if query.intent is not None
    )

    summary: StrategyEvaluationSummary = {
        "strategy": strategy_name,
        "total_questions": evaluation["total_questions"],
        "top_k": evaluation["top_k"],
        "hit_rate_at_k": evaluation["hit_rate_at_k"],
        "mean_reciprocal_rank": evaluation["mean_reciprocal_rank"],
        "negative_constraint_pass_rate": evaluation["negative_constraint_pass_rate"],
        "failed_question_ids": list(evaluation["failed_question_ids"]),
        "forbidden_hit_question_ids": list(evaluation["forbidden_hit_question_ids"]),
        "query_build_latency_seconds": query_build_latency,
        "retrieval_latency_seconds": retrieval_latency,
        "total_latency_seconds": query_build_latency + retrieval_latency,
        "model_call_count": nano_stats.model_call_count,
        "cache_hit_count": nano_stats.cache_hit_count,
        "cache_miss_count": nano_stats.cache_miss_count,
        "fallback_count": nano_stats.fallback_count,
        "structured_output_failure_count": nano_stats.structured_output_failure_count,
        "model_error_count": nano_stats.model_error_count,
        "unknown_tag_count": nano_stats.unknown_tag_count,
        "unmapped_tag_count": unmapped_count,
        "semantic_intent_micro_precision": semantic_intent_metrics[
            "precision"
        ],
        "semantic_intent_micro_recall": semantic_intent_metrics["recall"],
        "semantic_intent_exact_match_rate": semantic_intent_metrics[
            "exact_match_rate"
        ],
        "per_semantic_tag_metrics": semantic_intent_metrics["per_tag"],
        "intent_micro_precision": intent_metrics["precision"],
        "intent_micro_recall": intent_metrics["recall"],
        "intent_exact_match_rate": intent_metrics["exact_match_rate"],
        "per_tag_metrics": intent_metrics["per_tag"],
    }
    return {"summary": summary, "question_results": question_results}


def transform_question(
    question: RetrievalHoldoutQuestion,
    built_query: BuiltRetrievalQuery,
    *,
    strategy_name: StrategyName,
) -> RetrievalHoldoutQuestion:
    forbidden = list(question.get("forbidden_source_ids", []))
    transformed: RetrievalHoldoutQuestion = {
        "question_id": question["question_id"],
        "query": built_query.search_text,
        "expected_source_ids": list(question["expected_source_ids"]),
        "forbidden_source_ids": forbidden,
    }
    if "rationale" in question:
        transformed["rationale"] = question["rationale"]
    if "expected_semantic_intent_tags" in question:
        transformed["expected_semantic_intent_tags"] = list(
            question["expected_semantic_intent_tags"]
        )
    if "expected_intent_tags" in question:
        transformed["expected_intent_tags"] = list(question["expected_intent_tags"])
    return transformed


def enrich_question_results(
    *,
    original_questions: list[RetrievalHoldoutQuestion],
    evaluation: RetrievalHoldoutEvaluationResult,
    built_queries: dict[str, BuiltRetrievalQuery],
    fallback_by_question: dict[str, bool],
) -> list[StrategyQuestionResult]:
    questions_by_id = {
        question["question_id"]: question
        for question in original_questions
    }
    output: list[StrategyQuestionResult] = []
    for result in evaluation["question_results"]:
        question_id = result["question_id"]
        original = questions_by_id[question_id]
        built = built_queries[question_id]

        predicted_semantic = (
            [tag.value for tag in built.semantic_intent.tags]
            if built.semantic_intent is not None
            else []
        )
        expected_semantic = list(
            original.get("expected_semantic_intent_tags", [])
        )
        semantic_exact: bool | None = None
        if expected_semantic and built.semantic_intent is not None:
            semantic_exact = set(predicted_semantic) == set(expected_semantic)

        predicted = (
            [tag.value for tag in built.intent.tags]
            if built.intent is not None
            else []
        )
        expected = list(original.get("expected_intent_tags", []))
        exact: bool | None = None
        if expected and built.intent is not None:
            exact = set(predicted) == set(expected)

        output.append(
            {
                "question_id": question_id,
                "original_query": original["query"],
                "search_text": built.search_text,
                "predicted_semantic_intent_tags": predicted_semantic,
                "expected_semantic_intent_tags": expected_semantic,
                "semantic_intent_exact_match": semantic_exact,
                "predicted_intent_tags": predicted,
                "expected_intent_tags": expected,
                "intent_exact_match": exact,
                "expected_source_ids": list(result["expected_source_ids"]),
                "forbidden_source_ids": list(result["forbidden_source_ids"]),
                "retrieved_source_ids": list(result["retrieved_source_ids"]),
                "hit": result["hit"],
                "reciprocal_rank": result["reciprocal_rank"],
                "forbidden_source_hits": list(result["forbidden_source_hits"]),
                "negative_constraints_passed": result[
                    "negative_constraints_passed"
                ],
                "used_fallback": fallback_by_question[question_id],
            }
        )
    return output


def calculate_semantic_intent_metrics(
    results: list[StrategyQuestionResult],
) -> dict[str, Any]:
    rows = [
        (
            result["predicted_semantic_intent_tags"],
            result["expected_semantic_intent_tags"],
            result["semantic_intent_exact_match"],
        )
        for result in results
    ]
    return calculate_tag_metrics(
        rows,
        [tag.value for tag in SemanticIntentTag],
    )


def calculate_intent_metrics(
    results: list[StrategyQuestionResult],
) -> dict[str, Any]:
    rows = [
        (
            result["predicted_intent_tags"],
            result["expected_intent_tags"],
            result["intent_exact_match"],
        )
        for result in results
    ]
    return calculate_tag_metrics(
        rows,
        [tag.value for tag in RetrievalIntentTag],
    )


def calculate_tag_metrics(
    rows: list[tuple[list[str], list[str], bool | None]],
    known_tags: list[str],
) -> dict[str, Any]:
    scored = [row for row in rows if row[2] is not None]
    if not scored:
        return {
            "precision": None,
            "recall": None,
            "exact_match_rate": None,
            "per_tag": {},
        }

    expected_total = 0
    predicted_total = 0
    true_positive_total = 0
    exact_matches = 0
    counts = {
        tag: {"tp": 0, "predicted": 0, "expected": 0}
        for tag in sorted(known_tags)
    }

    for predicted_values, expected_values, _ in scored:
        predicted = set(predicted_values)
        expected = set(expected_values)
        intersection = predicted & expected
        expected_total += len(expected)
        predicted_total += len(predicted)
        true_positive_total += len(intersection)
        exact_matches += int(predicted == expected)
        for tag in predicted:
            counts[tag]["predicted"] += 1
        for tag in expected:
            counts[tag]["expected"] += 1
        for tag in intersection:
            counts[tag]["tp"] += 1

    per_tag: dict[str, IntentMetric] = {}
    for tag, values in counts.items():
        if values["predicted"] == 0 and values["expected"] == 0:
            continue
        per_tag[tag] = {
            "precision": safe_divide(values["tp"], values["predicted"]),
            "recall": safe_divide(values["tp"], values["expected"]),
            "true_positive": values["tp"],
            "predicted": values["predicted"],
            "expected": values["expected"],
        }

    return {
        "precision": safe_divide(true_positive_total, predicted_total),
        "recall": safe_divide(true_positive_total, expected_total),
        "exact_match_rate": exact_matches / len(scored),
        "per_tag": per_tag,
    }


def safe_divide(numerator: int, denominator: int) -> float:
    return 0.0 if denominator == 0 else numerator / denominator


def build_nano_client(model_name: str | None) -> OpenAIJsonClient:
    if model_name is None:
        return openai_json_client_from_env()
    return OpenAIJsonClient(model=model_name)


def format_comparison_markdown(
    comparison: RetrievalAblationResult,
    strategy_results: list[StrategyEvaluationResult],
) -> str:
    lines = [
        "# Controlled Retrieval Intent Ablation",
        "",
        f"Generated: `{comparison['generated_at']}`",
        f"Run ID: `{comparison['run_id']}`",
        f"Question count: `{comparison['question_count']}`",
        f"Top K: `{comparison['top_k']}`",
        f"Nano model: `{comparison['nano_model'] or 'not used'}`",
        f"Intent schema: `{comparison['intent_schema_version']}`",
        "",
        "## Summary",
        "",
        "| Strategy | Hit Rate@K | MRR | Negative Pass | Semantic P | Semantic R | Semantic Exact | Derived Exact | Seconds | Calls | Cache | Fallbacks |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for summary in comparison["summaries"]:
        lines.append(
            "| "
            f"{summary['strategy']} | "
            f"{summary['hit_rate_at_k']:.3f} | "
            f"{summary['mean_reciprocal_rank']:.3f} | "
            f"{summary['negative_constraint_pass_rate']:.3f} | "
            f"{format_optional(summary['semantic_intent_micro_precision'])} | "
            f"{format_optional(summary['semantic_intent_micro_recall'])} | "
            f"{format_optional(summary['semantic_intent_exact_match_rate'])} | "
            f"{format_optional(summary['intent_exact_match_rate'])} | "
            f"{summary['total_latency_seconds']:.3f} | "
            f"{summary['model_call_count']} | "
            f"{summary['cache_hit_count']} | "
            f"{summary['fallback_count']} |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Corpus, chunks, retriever, scoring, top-K, and source labels are held constant.",
            "- Rule and nano detectors predict semantic tags only.",
            "- Deterministic policy derives workflow tags before the shared mapper runs.",
            "- Legacy deterministic expansion remains a comparator.",
            "- Do not tune against the frozen holdout.",
            "",
        ]
    )
    return "\n".join(lines)


def format_optional(value: float | None) -> str:
    return "-" if value is None else f"{value:.3f}"


def normalize_run_id(value: str) -> str:
    clean = value.strip()
    if not clean:
        raise ValueError("run_id must not be blank")
    if any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in clean):
        raise ValueError("run_id may contain only letters, numbers, hyphens, and underscores")
    return clean


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
