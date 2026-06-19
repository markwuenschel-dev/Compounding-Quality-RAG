from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import NotRequired, TypedDict

from app.retrieval import DEFAULT_CHUNKS_PATH, Retriever
from app.retrieval_intent import (
    RetrievalIntent,
    SemanticRetrievalIntent,
)
from app.retrieval_evaluate import (
    RetrievalQuestion,
    evaluate_retrieval_questions,
    parse_retrieval_question,
)
from app.review_summary_evaluate import (
    ReviewSummaryEvaluationResult,
    build_live_extractor,
    evaluate_review_summary_extraction_cases,
    format_evaluation_report,
    load_review_summary_extraction_cases,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXTRACTION_HOLDOUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "eval"
    / "review_summary_extraction_holdout.json"
)
DEFAULT_RETRIEVAL_HOLDOUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "eval"
    / "retrieval_questions_holdout.json"
)
DEFAULT_RETRIEVAL_DEVELOPMENT_PATH = (
    PROJECT_ROOT
    / "data"
    / "eval"
    / "retrieval_questions_development.json"
)
DEFAULT_RETRIEVAL_ABLATION_ARTIFACTS_ROOT = (
    PROJECT_ROOT
    / "artifacts"
    / "runs"
)
DEFAULT_EXTRACTION_REPORT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "review_summary_extraction_holdout.md"
)
DEFAULT_RETRIEVAL_REPORT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "retrieval_holdout.md"
)
DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT
    / "data"
    / "eval"
    / "holdout_manifest.json"
)


class RetrievalHoldoutQuestion(RetrievalQuestion):
    forbidden_source_ids: NotRequired[list[str]]
    rationale: NotRequired[str]
    expected_semantic_intent_tags: NotRequired[list[str]]
    expected_intent_tags: NotRequired[list[str]]


class RetrievalHoldoutQuestionResult(TypedDict):
    question_id: str
    query: str
    rationale: str | None
    expected_source_ids: list[str]
    forbidden_source_ids: list[str]
    retrieved_source_ids: list[str]
    hit: bool
    reciprocal_rank: float
    forbidden_source_hits: list[str]
    negative_constraints_passed: bool


class RetrievalHoldoutEvaluationResult(TypedDict):
    total_questions: int
    top_k: int
    hit_rate_at_k: float
    mean_reciprocal_rank: float
    negative_constraint_pass_rate: float
    failed_question_ids: list[str]
    forbidden_hit_question_ids: list[str]
    question_results: list[RetrievalHoldoutQuestionResult]


class HoldoutManifestFile(TypedDict):
    path: str
    sha256: str
    item_count: int


class HoldoutManifest(TypedDict):
    frozen_at: str
    files: list[HoldoutManifestFile]
    instructions: str


def load_retrieval_holdout_questions(
    questions_path: Path = DEFAULT_RETRIEVAL_HOLDOUT_PATH,
) -> list[RetrievalHoldoutQuestion]:
    if not questions_path.exists():
        raise FileNotFoundError(
            f"Retrieval holdout file does not exist: {questions_path}"
        )

    raw_data = json.loads(questions_path.read_text(encoding="utf-8"))

    if not isinstance(raw_data, list):
        raise ValueError("Retrieval holdout file must contain a JSON list")

    questions = [
        parse_retrieval_holdout_question(raw_question, index)
        for index, raw_question in enumerate(raw_data)
    ]

    if not questions:
        raise ValueError("Retrieval holdout file must contain at least one question")

    return questions


def parse_retrieval_holdout_question(
    raw_question: object,
    index: int,
) -> RetrievalHoldoutQuestion:
    base_question = parse_retrieval_question(raw_question, index)

    if not isinstance(raw_question, dict):
        raise ValueError(
            f"Retrieval holdout question at index {index} must be an object"
        )

    forbidden_raw = raw_question.get("forbidden_source_ids", [])
    rationale_raw = raw_question.get("rationale")
    expected_semantic_intent_raw = raw_question.get(
        "expected_semantic_intent_tags"
    )
    expected_intent_raw = raw_question.get("expected_intent_tags")

    if not isinstance(forbidden_raw, list):
        raise ValueError(
            f"Retrieval question {base_question['question_id']} "
            "forbidden_source_ids must be a list"
        )

    forbidden_source_ids = [str(value) for value in forbidden_raw]
    overlap = sorted(
        set(base_question["expected_source_ids"])
        & set(forbidden_source_ids)
    )

    if overlap:
        raise ValueError(
            f"Retrieval question {base_question['question_id']} "
            f"cannot expect and forbid the same sources: {overlap}"
        )

    question: RetrievalHoldoutQuestion = {
        **base_question,
        "forbidden_source_ids": forbidden_source_ids,
    }

    if expected_semantic_intent_raw is not None:
        if not isinstance(expected_semantic_intent_raw, list):
            raise ValueError(
                f"Retrieval question {base_question['question_id']} "
                "expected_semantic_intent_tags must be a list"
            )
        validated_semantic_intent = (
            SemanticRetrievalIntent.model_validate(
                {"tags": expected_semantic_intent_raw}
            )
        )
        question["expected_semantic_intent_tags"] = [
            tag.value for tag in validated_semantic_intent.tags
        ]

    if expected_intent_raw is not None:
        if not isinstance(expected_intent_raw, list):
            raise ValueError(
                f"Retrieval question {base_question['question_id']} "
                "expected_intent_tags must be a list"
            )
        validated_intent = RetrievalIntent.model_validate(
            {"tags": expected_intent_raw}
        )
        question["expected_intent_tags"] = [
            tag.value for tag in validated_intent.tags
        ]

    if rationale_raw is not None:
        rationale = str(rationale_raw).strip()

        if not rationale:
            raise ValueError(
                f"Retrieval question {base_question['question_id']} "
                "rationale must not be blank"
            )

        question["rationale"] = rationale

    return question


def evaluate_retrieval_holdout(
    questions: list[RetrievalHoldoutQuestion],
    *,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    top_k: int = 5,
    retriever: Retriever | None = None,
) -> RetrievalHoldoutEvaluationResult:
    if not questions:
        raise ValueError("questions must contain at least one retrieval question")

    base_questions: list[RetrievalQuestion] = [
        {
            "question_id": question["question_id"],
            "query": question["query"],
            "expected_source_ids": question["expected_source_ids"],
        }
        for question in questions
    ]

    base_result = evaluate_retrieval_questions(
        base_questions,
        chunks_path=chunks_path,
        top_k=top_k,
        retriever=retriever,
    )
    questions_by_id = {
        question["question_id"]: question
        for question in questions
    }

    question_results: list[RetrievalHoldoutQuestionResult] = []

    for base_question_result in base_result["question_results"]:
        question = questions_by_id[base_question_result["question_id"]]
        forbidden_source_ids = question.get("forbidden_source_ids", [])
        forbidden_hits = [
            source_id
            for source_id in base_question_result["retrieved_source_ids"]
            if source_id in set(forbidden_source_ids)
        ]

        question_results.append(
            {
                "question_id": base_question_result["question_id"],
                "query": base_question_result["query"],
                "rationale": question.get("rationale"),
                "expected_source_ids": base_question_result[
                    "expected_source_ids"
                ],
                "forbidden_source_ids": forbidden_source_ids,
                "retrieved_source_ids": base_question_result[
                    "retrieved_source_ids"
                ],
                "hit": base_question_result["hit"],
                "reciprocal_rank": base_question_result[
                    "reciprocal_rank"
                ],
                "forbidden_source_hits": forbidden_hits,
                "negative_constraints_passed": not forbidden_hits,
            }
        )

    forbidden_hit_question_ids = [
        result["question_id"]
        for result in question_results
        if not result["negative_constraints_passed"]
    ]

    return {
        "total_questions": base_result["total_questions"],
        "top_k": base_result["top_k"],
        "hit_rate_at_k": base_result["hit_rate_at_k"],
        "mean_reciprocal_rank": base_result[
            "mean_reciprocal_rank"
        ],
        "negative_constraint_pass_rate": (
            sum(
                1
                for result in question_results
                if result["negative_constraints_passed"]
            )
            / len(question_results)
        ),
        "failed_question_ids": base_result[
            "failed_question_ids"
        ],
        "forbidden_hit_question_ids": forbidden_hit_question_ids,
        "question_results": question_results,
    }


def format_retrieval_holdout_report(
    result: RetrievalHoldoutEvaluationResult,
) -> str:
    lines = [
        "# Retrieval Holdout Evaluation",
        "",
        f"Generated: `{utc_timestamp()}`",
        f"Question count: `{result['total_questions']}`",
        f"Top K: `{result['top_k']}`",
        "",
        "## Summary",
        "",
        "| Metric | Score |",
        "|---|---:|",
        f"| Hit rate at K | {result['hit_rate_at_k']:.3f} |",
        f"| Mean reciprocal rank | {result['mean_reciprocal_rank']:.3f} |",
        (
            "| Negative-constraint pass rate | "
            f"{result['negative_constraint_pass_rate']:.3f} |"
        ),
        "",
        "## Failed expected-source questions",
        "",
        format_ids(result["failed_question_ids"]),
        "",
        "## Questions with forbidden-source hits",
        "",
        format_ids(result["forbidden_hit_question_ids"]),
        "",
    ]

    failed_ids = set(result["failed_question_ids"])
    forbidden_ids = set(result["forbidden_hit_question_ids"])

    for question_result in result["question_results"]:
        if (
            question_result["question_id"] not in failed_ids
            and question_result["question_id"] not in forbidden_ids
        ):
            continue

        lines.extend(
            [
                f"### {question_result['question_id']}",
                "",
                f"> {question_result['query']}",
                "",
                (
                    f"- Rationale: "
                    f"{question_result['rationale'] or 'Not provided'}"
                ),
                (
                    "- Expected sources: "
                    f"{format_values(question_result['expected_source_ids'])}"
                ),
                (
                    "- Retrieved sources: "
                    f"{format_values(question_result['retrieved_source_ids'])}"
                ),
                (
                    "- Forbidden sources: "
                    f"{format_values(question_result['forbidden_source_ids'])}"
                ),
                (
                    "- Forbidden hits: "
                    f"{format_values(question_result['forbidden_source_hits'])}"
                ),
                (
                    "- Reciprocal rank: "
                    f"{question_result['reciprocal_rank']:.3f}"
                ),
                "",
            ]
        )

    lines.extend(
        [
            "## Interpretation guardrails",
            "",
            "- Record the baseline before changing retrieval, SOPs, or chunking.",
            "- A forbidden-source hit means a known irrelevant source entered the top-K results.",
            "- Source-level relevance does not prove that the exact retrieved section is correct.",
            "- Use failed cases to decide whether the bottleneck is corpus coverage, scoring, or chunk boundaries.",
            "",
        ]
    )

    return "\n".join(lines)


def format_extraction_holdout_report(
    result: ReviewSummaryEvaluationResult,
) -> str:
    report = format_evaluation_report(result)

    return report.replace(
        "# Review Summary Extraction Evaluation",
        "# Review Summary Extraction Holdout Evaluation",
        1,
    )


def validate_holdout_files(
    *,
    extraction_cases_path: Path,
    retrieval_questions_path: Path,
) -> dict[str, int]:
    extraction_cases = load_review_summary_extraction_cases(
        extraction_cases_path
    )
    retrieval_questions = load_retrieval_holdout_questions(
        retrieval_questions_path
    )

    return {
        "extraction_case_count": len(extraction_cases),
        "retrieval_question_count": len(retrieval_questions),
    }


def freeze_holdout_files(
    *,
    extraction_cases_path: Path,
    retrieval_questions_path: Path,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> HoldoutManifest:
    counts = validate_holdout_files(
        extraction_cases_path=extraction_cases_path,
        retrieval_questions_path=retrieval_questions_path,
    )
    files: list[HoldoutManifestFile] = [
        {
            "path": display_path(extraction_cases_path),
            "sha256": sha256_file(extraction_cases_path),
            "item_count": counts["extraction_case_count"],
        },
        {
            "path": display_path(retrieval_questions_path),
            "sha256": sha256_file(retrieval_questions_path),
            "item_count": counts["retrieval_question_count"],
        },
    ]
    manifest: HoldoutManifest = {
        "frozen_at": utc_timestamp(),
        "files": files,
        "instructions": (
            "Treat these hashes as the pre-tuning baseline. "
            "Record results before changing prompts, grounding, "
            "retrieval scoring, corpus content, or chunking."
        ),
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    return manifest


def run_extraction_holdout(
    *,
    cases_path: Path = DEFAULT_EXTRACTION_HOLDOUT_PATH,
    report_path: Path = DEFAULT_EXTRACTION_REPORT_PATH,
) -> ReviewSummaryEvaluationResult:
    cases = load_review_summary_extraction_cases(cases_path)
    result = evaluate_review_summary_extraction_cases(
        cases,
        extractor=build_live_extractor(),
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        format_extraction_holdout_report(result),
        encoding="utf-8",
    )

    return result


def run_retrieval_holdout(
    *,
    questions_path: Path = DEFAULT_RETRIEVAL_HOLDOUT_PATH,
    report_path: Path = DEFAULT_RETRIEVAL_REPORT_PATH,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    top_k: int = 5,
    retriever: Retriever | None = None,
) -> RetrievalHoldoutEvaluationResult:
    questions = load_retrieval_holdout_questions(
        questions_path
    )
    result = evaluate_retrieval_holdout(
        questions,
        chunks_path=chunks_path,
        top_k=top_k,
        retriever=retriever,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        format_retrieval_holdout_report(result),
        encoding="utf-8",
    )

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate, freeze, and run unseen extraction and "
            "retrieval holdout datasets."
        )
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate both holdout fixture files without running models.",
    )
    add_fixture_arguments(validate_parser)

    freeze_parser = subparsers.add_parser(
        "freeze",
        help="Validate the fixtures and write a SHA-256 manifest.",
    )
    add_fixture_arguments(freeze_parser)
    freeze_parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
    )

    extraction_parser = subparsers.add_parser(
        "extraction",
        help="Run the live review-summary extraction holdout.",
    )
    extraction_parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_EXTRACTION_HOLDOUT_PATH,
    )
    extraction_parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_EXTRACTION_REPORT_PATH,
    )

    retrieval_parser = subparsers.add_parser(
        "retrieval",
        help="Run the keyword retrieval holdout.",
    )
    retrieval_parser.add_argument(
        "--questions",
        type=Path,
        default=DEFAULT_RETRIEVAL_HOLDOUT_PATH,
    )
    retrieval_parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_RETRIEVAL_REPORT_PATH,
    )
    retrieval_parser.add_argument(
        "--chunks",
        type=Path,
        default=DEFAULT_CHUNKS_PATH,
    )
    retrieval_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
    )

    ablation_parser = subparsers.add_parser(
        "retrieval-ablation",
        help=(
            "Compare raw, legacy deterministic, rule-intent, and "
            "nano-intent query strategies on a retrieval fixture set."
        ),
    )
    ablation_parser.add_argument(
        "--questions",
        type=Path,
        default=DEFAULT_RETRIEVAL_DEVELOPMENT_PATH,
    )
    ablation_parser.add_argument(
        "--chunks",
        type=Path,
        default=DEFAULT_CHUNKS_PATH,
    )
    ablation_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
    )
    ablation_parser.add_argument(
        "--strategies",
        default=(
            "raw,deterministic_expansion,rule_intent,nano_intent"
        ),
    )
    ablation_parser.add_argument(
        "--run-id",
        default="retrieval-dev-ablation",
    )
    ablation_parser.add_argument(
        "--artifacts-root",
        type=Path,
        default=DEFAULT_RETRIEVAL_ABLATION_ARTIFACTS_ROOT,
    )
    ablation_parser.add_argument(
        "--nano-model",
        default=None,
    )
    ablation_parser.add_argument(
        "--refresh-nano",
        action="store_true",
    )

    all_parser = subparsers.add_parser(
        "all",
        help="Run both holdouts and write both reports.",
    )
    add_fixture_arguments(all_parser)
    all_parser.add_argument(
        "--extraction-report",
        type=Path,
        default=DEFAULT_EXTRACTION_REPORT_PATH,
    )
    all_parser.add_argument(
        "--retrieval-report",
        type=Path,
        default=DEFAULT_RETRIEVAL_REPORT_PATH,
    )
    all_parser.add_argument(
        "--chunks",
        type=Path,
        default=DEFAULT_CHUNKS_PATH,
    )
    all_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
    )

    return parser


def add_fixture_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--extraction-cases",
        type=Path,
        default=DEFAULT_EXTRACTION_HOLDOUT_PATH,
    )
    parser.add_argument(
        "--retrieval-questions",
        type=Path,
        default=DEFAULT_RETRIEVAL_HOLDOUT_PATH,
    )


def main() -> None:
    args = build_parser().parse_args()
    result: object

    if args.command == "validate":
        result = validate_holdout_files(
            extraction_cases_path=args.extraction_cases,
            retrieval_questions_path=args.retrieval_questions,
        )
    elif args.command == "freeze":
        result = freeze_holdout_files(
            extraction_cases_path=args.extraction_cases,
            retrieval_questions_path=args.retrieval_questions,
            manifest_path=args.manifest,
        )
    elif args.command == "extraction":
        result = run_extraction_holdout(
            cases_path=args.cases,
            report_path=args.report,
        )
    elif args.command == "retrieval":
        result = run_retrieval_holdout(
            questions_path=args.questions,
            report_path=args.report,
            chunks_path=args.chunks,
            top_k=args.top_k,
        )
    elif args.command == "retrieval-ablation":
        from app.retrieval_ablation import (
            parse_strategy_names,
            run_retrieval_ablation,
        )

        result = run_retrieval_ablation(
            questions_path=args.questions,
            chunks_path=args.chunks,
            top_k=args.top_k,
            strategy_names=parse_strategy_names(
                args.strategies
            ),
            run_id=args.run_id,
            artifacts_root=args.artifacts_root,
            nano_model=args.nano_model,
            refresh_nano=args.refresh_nano,
        )
    else:
        extraction_result = run_extraction_holdout(
            cases_path=args.extraction_cases,
            report_path=args.extraction_report,
        )
        retrieval_result = run_retrieval_holdout(
            questions_path=args.retrieval_questions,
            report_path=args.retrieval_report,
            chunks_path=args.chunks,
            top_k=args.top_k,
        )
        result = {
            "extraction": extraction_result,
            "retrieval": retrieval_result,
        }

    print(json.dumps(result, indent=2))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())

    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def format_ids(values: list[str]) -> str:
    return "None" if not values else ", ".join(values)


def format_values(values: list[str]) -> str:
    return "None" if not values else ", ".join(f"`{value}`" for value in values)


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")


if __name__ == "__main__":
    main()
