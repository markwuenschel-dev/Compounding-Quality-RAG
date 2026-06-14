from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict

from app.llm_client import openai_json_client_from_env
from app.review_summary_extraction import extract_review_summary_result
from app.schemas import ReviewSummary, ReviewSummaryExtractionResult


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_PATH = (
    PROJECT_ROOT
    / "data"
    / "eval"
    / "review_summary_extraction_cases.json"
)
DEFAULT_REPORT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "review_summary_extraction_evaluation.md"
)

SCALAR_FIELDS = (
    "record_review_result",
    "lot_batch_pattern_summary",
    "inventory_inspection_result",
    "api_reference_review_result",
)


class ReviewSummaryExtractionCase(TypedDict):
    case_id: str
    concern_text: str
    reviewer_note: str
    expected_review_summary: dict[str, Any]
    expected_unresolved_field_names: list[str]


class ScalarMismatch(TypedDict):
    field_name: str
    expected: str
    actual: str


class CaseEvaluationResult(TypedDict):
    case_id: str
    concern_text: str
    reviewer_note: str
    scalar_correct: int
    scalar_total: int
    scalar_mismatches: list[ScalarMismatch]
    missing_information_precision: float
    missing_information_recall: float
    missing_information_false_positives: list[str]
    missing_information_false_negatives: list[str]
    severe_trigger_precision: float
    severe_trigger_recall: float
    severe_trigger_false_positives: list[str]
    severe_trigger_false_negatives: list[str]
    unresolved_question_precision: float
    unresolved_question_recall: float
    unresolved_question_false_positives: list[str]
    unresolved_question_false_negatives: list[str]


class ReviewSummaryEvaluationResult(TypedDict):
    generated_at: str
    case_count: int
    scalar_field_accuracy: float
    missing_information_precision: float
    missing_information_recall: float
    severe_trigger_precision: float
    severe_trigger_recall: float
    unresolved_question_precision: float
    unresolved_question_recall: float
    failed_case_ids: list[str]
    case_results: list[CaseEvaluationResult]


Extractor = Callable[
    [str, str],
    ReviewSummaryExtractionResult,
]


def load_review_summary_extraction_cases(
    cases_path: Path = DEFAULT_CASES_PATH,
) -> list[ReviewSummaryExtractionCase]:
    if not cases_path.exists():
        raise FileNotFoundError(
            f"Review-summary extraction cases file does not exist: {cases_path}"
        )

    raw_data = json.loads(cases_path.read_text(encoding="utf-8"))

    if not isinstance(raw_data, list):
        raise ValueError("Review-summary extraction cases must contain a JSON list")

    cases = [
        parse_case(raw_case, index)
        for index, raw_case in enumerate(raw_data)
    ]

    if not cases:
        raise ValueError("Review-summary extraction cases must not be empty")

    return cases


def parse_case(
    raw_case: object,
    index: int,
) -> ReviewSummaryExtractionCase:
    if not isinstance(raw_case, dict):
        raise ValueError(f"Extraction case at index {index} must be an object")

    required_keys = {
        "case_id",
        "concern_text",
        "reviewer_note",
        "expected_review_summary",
        "expected_unresolved_field_names",
    }
    missing_keys = required_keys - raw_case.keys()

    if missing_keys:
        raise ValueError(
            f"Extraction case at index {index} is missing keys: {sorted(missing_keys)}"
        )

    expected_review_summary = raw_case["expected_review_summary"]
    expected_unresolved_field_names = raw_case[
        "expected_unresolved_field_names"
    ]

    if not isinstance(expected_review_summary, dict):
        raise ValueError(
            f"Extraction case at index {index} expected_review_summary must be an object"
        )

    if not isinstance(expected_unresolved_field_names, list):
        raise ValueError(
            f"Extraction case at index {index} expected_unresolved_field_names must be a list"
        )

    ReviewSummary.model_validate(expected_review_summary)

    return {
        "case_id": str(raw_case["case_id"]),
        "concern_text": str(raw_case["concern_text"]),
        "reviewer_note": str(raw_case["reviewer_note"]),
        "expected_review_summary": expected_review_summary,
        "expected_unresolved_field_names": [
            str(value)
            for value in expected_unresolved_field_names
        ],
    }


def evaluate_review_summary_extraction_cases(
    cases: list[ReviewSummaryExtractionCase],
    *,
    extractor: Extractor,
) -> ReviewSummaryEvaluationResult:
    if not cases:
        raise ValueError("cases must not be empty")

    case_results = [
        evaluate_case(case, extractor=extractor)
        for case in cases
    ]

    scalar_correct = sum(
        result["scalar_correct"]
        for result in case_results
    )
    scalar_total = sum(
        result["scalar_total"]
        for result in case_results
    )

    failed_case_ids = [
        result["case_id"]
        for result in case_results
        if case_has_failure(result)
    ]

    return {
        "generated_at": utc_timestamp(),
        "case_count": len(case_results),
        "scalar_field_accuracy": scalar_correct / scalar_total,
        "missing_information_precision": mean(
            result["missing_information_precision"]
            for result in case_results
        ),
        "missing_information_recall": mean(
            result["missing_information_recall"]
            for result in case_results
        ),
        "severe_trigger_precision": mean(
            result["severe_trigger_precision"]
            for result in case_results
        ),
        "severe_trigger_recall": mean(
            result["severe_trigger_recall"]
            for result in case_results
        ),
        "unresolved_question_precision": mean(
            result["unresolved_question_precision"]
            for result in case_results
        ),
        "unresolved_question_recall": mean(
            result["unresolved_question_recall"]
            for result in case_results
        ),
        "failed_case_ids": failed_case_ids,
        "case_results": case_results,
    }


def evaluate_case(
    case: ReviewSummaryExtractionCase,
    *,
    extractor: Extractor,
) -> CaseEvaluationResult:
    expected = ReviewSummary.model_validate(
        case["expected_review_summary"]
    )
    actual_result = extractor(
        case["concern_text"],
        case["reviewer_note"],
    )
    actual = actual_result.review_summary

    scalar_mismatches = build_scalar_mismatches(
        expected=expected,
        actual=actual,
    )

    missing_comparison = compare_sets(
        expected.missing_information,
        actual.missing_information,
    )
    severe_comparison = compare_sets(
        [value.value for value in expected.severe_triggers_observed],
        [value.value for value in actual.severe_triggers_observed],
    )
    unresolved_comparison = compare_sets(
        case["expected_unresolved_field_names"],
        [
            question.field_name
            for question in actual_result.unresolved_questions
        ],
    )

    return {
        "case_id": case["case_id"],
        "concern_text": case["concern_text"],
        "reviewer_note": case["reviewer_note"],
        "scalar_correct": len(SCALAR_FIELDS) - len(scalar_mismatches),
        "scalar_total": len(SCALAR_FIELDS),
        "scalar_mismatches": scalar_mismatches,
        "missing_information_precision": missing_comparison["precision"],
        "missing_information_recall": missing_comparison["recall"],
        "missing_information_false_positives": missing_comparison["false_positives"],
        "missing_information_false_negatives": missing_comparison["false_negatives"],
        "severe_trigger_precision": severe_comparison["precision"],
        "severe_trigger_recall": severe_comparison["recall"],
        "severe_trigger_false_positives": severe_comparison["false_positives"],
        "severe_trigger_false_negatives": severe_comparison["false_negatives"],
        "unresolved_question_precision": unresolved_comparison["precision"],
        "unresolved_question_recall": unresolved_comparison["recall"],
        "unresolved_question_false_positives": unresolved_comparison["false_positives"],
        "unresolved_question_false_negatives": unresolved_comparison["false_negatives"],
    }


def build_scalar_mismatches(
    *,
    expected: ReviewSummary,
    actual: ReviewSummary,
) -> list[ScalarMismatch]:
    mismatches: list[ScalarMismatch] = []

    for field_name in SCALAR_FIELDS:
        expected_value = getattr(expected, field_name).value
        actual_value = getattr(actual, field_name).value

        if expected_value == actual_value:
            continue

        mismatches.append(
            {
                "field_name": field_name,
                "expected": expected_value,
                "actual": actual_value,
            }
        )

    return mismatches


def compare_sets(
    expected_values: Iterable[str],
    actual_values: Iterable[str],
) -> dict[str, Any]:
    expected = set(expected_values)
    actual = set(actual_values)
    true_positives = len(expected & actual)

    precision = (
        true_positives / len(actual)
        if actual
        else 1.0 if not expected else 0.0
    )
    recall = (
        true_positives / len(expected)
        if expected
        else 1.0
    )

    return {
        "precision": precision,
        "recall": recall,
        "false_positives": sorted(actual - expected),
        "false_negatives": sorted(expected - actual),
    }


def case_has_failure(result: CaseEvaluationResult) -> bool:
    return any(
        (
            result["scalar_mismatches"],
            result["missing_information_false_positives"],
            result["missing_information_false_negatives"],
            result["severe_trigger_false_positives"],
            result["severe_trigger_false_negatives"],
            result["unresolved_question_false_positives"],
            result["unresolved_question_false_negatives"],
        )
    )


def format_evaluation_report(
    result: ReviewSummaryEvaluationResult,
) -> str:
    lines = [
        "# Review Summary Extraction Evaluation",
        "",
        f"Generated: `{result['generated_at']}`",
        f"Case count: `{result['case_count']}`",
        "",
        "## Summary",
        "",
        "| Metric | Score |",
        "|---|---:|",
        f"| Scalar field accuracy | {result['scalar_field_accuracy']:.3f} |",
        f"| Missing-information precision | {result['missing_information_precision']:.3f} |",
        f"| Missing-information recall | {result['missing_information_recall']:.3f} |",
        f"| Severe-trigger precision | {result['severe_trigger_precision']:.3f} |",
        f"| Severe-trigger recall | {result['severe_trigger_recall']:.3f} |",
        f"| Unresolved-question precision | {result['unresolved_question_precision']:.3f} |",
        f"| Unresolved-question recall | {result['unresolved_question_recall']:.3f} |",
        "",
        "## Failed cases",
        "",
        format_failed_ids(result["failed_case_ids"]),
        "",
    ]

    failed_results = [
        case_result
        for case_result in result["case_results"]
        if case_has_failure(case_result)
    ]

    if failed_results:
        lines.extend(
            [
                "## Failure diagnostics",
                "",
            ]
        )

        for case_result in failed_results:
            lines.extend(format_case_diagnostics(case_result))

    lines.extend(
        [
            "## Guardrails",
            "",
            "- Severe-trigger false positives and false negatives require manual review.",
            "- Numeric model confidence is intentionally not reported because it has not been calibrated.",
            "- Supporting quotes must come directly from the reviewer note.",
            "- This evaluation uses synthetic cases and does not establish production clinical performance.",
            "",
        ]
    )

    return "\n".join(lines)


def format_case_diagnostics(
    result: CaseEvaluationResult,
) -> list[str]:
    lines = [
        f"### {result['case_id']}",
        "",
        "**Concern**",
        "",
        quote_markdown(result["concern_text"]),
        "",
        "**Reviewer note**",
        "",
        quote_markdown(result["reviewer_note"]),
        "",
    ]

    if result["scalar_mismatches"]:
        lines.extend(
            [
                "**Scalar mismatches**",
                "",
                "| Field | Expected | Actual |",
                "|---|---|---|",
            ]
        )

        for mismatch in result["scalar_mismatches"]:
            lines.append(
                f"| `{mismatch['field_name']}` | "
                f"`{mismatch['expected']}` | "
                f"`{mismatch['actual']}` |"
            )

        lines.append("")

    lines.extend(
        format_difference_section(
            title="Missing information",
            false_positives=result["missing_information_false_positives"],
            false_negatives=result["missing_information_false_negatives"],
        )
    )
    lines.extend(
        format_difference_section(
            title="Severe triggers",
            false_positives=result["severe_trigger_false_positives"],
            false_negatives=result["severe_trigger_false_negatives"],
        )
    )
    lines.extend(
        format_difference_section(
            title="Unresolved questions",
            false_positives=result["unresolved_question_false_positives"],
            false_negatives=result["unresolved_question_false_negatives"],
        )
    )

    return lines


def format_difference_section(
    *,
    title: str,
    false_positives: list[str],
    false_negatives: list[str],
) -> list[str]:
    if not false_positives and not false_negatives:
        return []

    return [
        f"**{title}**",
        "",
        f"- False positives: {format_values(false_positives)}",
        f"- False negatives: {format_values(false_negatives)}",
        "",
    ]


def quote_markdown(value: str) -> str:
    return "\n".join(
        f"> {line}"
        for line in value.splitlines()
    )


def format_values(values: list[str]) -> str:
    if not values:
        return "None"

    return ", ".join(f"`{value}`" for value in values)


def write_evaluation_report(
    result: ReviewSummaryEvaluationResult,
    *,
    output_path: Path = DEFAULT_REPORT_PATH,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        format_evaluation_report(result),
        encoding="utf-8",
    )

    return output_path


def build_live_extractor() -> Extractor:
    client = openai_json_client_from_env()

    def extract(
        concern_text: str,
        reviewer_note: str,
    ) -> ReviewSummaryExtractionResult:
        return extract_review_summary_result(
            reviewer_note=reviewer_note,
            llm_client=client,
            concern_text=concern_text,
        )

    return extract


def mean(values: Iterable[float]) -> float:
    collected = list(values)

    if not collected:
        raise ValueError("values must not be empty")

    return sum(collected) / len(collected)


def format_failed_ids(failed_case_ids: list[str]) -> str:
    if not failed_case_ids:
        return "None"

    return ", ".join(failed_case_ids)


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> None:
    cases = load_review_summary_extraction_cases()
    result = evaluate_review_summary_extraction_cases(
        cases,
        extractor=build_live_extractor(),
    )
    write_evaluation_report(result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
