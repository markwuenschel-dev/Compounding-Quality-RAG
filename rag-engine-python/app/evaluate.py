from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from pathlib import Path
from typing import Any, TypedDict

from pydantic import BaseModel

from app.schemas import ExpectedStructuredOutput


DEFAULT_EXACT_MATCH_FIELD_PATHS = (
    "derived_assessment.reviewer_assigned_classification",
    "derived_assessment.reviewer_assigned_category",
    "derived_assessment.reviewer_assigned_subcategory",
    "derived_assessment.concern_type",
    "derived_assessment.risk_lane",
    "derived_assessment.review_scope",
    "derived_assessment.handling_path",
    "derived_assessment.escalation_triggers",
    "derived_assessment.resolution_review_required",
    "derived_assessment.resolution_options",
)


class FieldComparison(TypedDict):
    field_path: str
    expected: Any
    actual: Any
    passed: bool


class EvaluationResult(TypedDict):
    passed: bool
    comparisons: list[FieldComparison]
    failed_fields: list[str]


def load_expected_output(expected_output_path: Path) -> ExpectedStructuredOutput:
    if not expected_output_path.exists():
        raise FileNotFoundError(
            f"Expected output file does not exist: {expected_output_path}"
        )

    return ExpectedStructuredOutput.model_validate_json(
        expected_output_path.read_text(encoding="utf-8")
    )


def evaluate_structured_output(
    *,
    expected: ExpectedStructuredOutput,
    actual: ExpectedStructuredOutput,
    field_paths: Sequence[str] = DEFAULT_EXACT_MATCH_FIELD_PATHS,
) -> EvaluationResult:
    comparisons: list[FieldComparison] = []

    for field_path in field_paths:
        expected_value = normalize_for_comparison(
            get_field_value(expected, field_path)
        )
        actual_value = normalize_for_comparison(
            get_field_value(actual, field_path)
        )

        comparisons.append(
            {
                "field_path": field_path,
                "expected": expected_value,
                "actual": actual_value,
                "passed": expected_value == actual_value,
            }
        )

    failed_fields = [
        comparison["field_path"]
        for comparison in comparisons
        if not comparison["passed"]
    ]

    return {
        "passed": not failed_fields,
        "comparisons": comparisons,
        "failed_fields": failed_fields,
    }


def get_field_value(obj: object, field_path: str) -> object:
    current = obj

    for field_name in field_path.split("."):
        if isinstance(current, dict):
            if field_name not in current:
                raise KeyError(f"Field path {field_path!r} failed at {field_name!r}")
            current = current[field_name]
            continue

        if not hasattr(current, field_name):
            raise AttributeError(
                f"Field path {field_path!r} failed at {field_name!r}"
            )

        current = getattr(current, field_name)

    return current


def normalize_for_comparison(value: object) -> object:
    if isinstance(value, Enum):
        return value.value

    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")

    if isinstance(value, list):
        return [normalize_for_comparison(item) for item in value]

    if isinstance(value, tuple):
        return [normalize_for_comparison(item) for item in value]

    if isinstance(value, dict):
        return {
            str(key): normalize_for_comparison(item)
            for key, item in value.items()
        }

    return value


def get_comparison(
    result: EvaluationResult,
    field_path: str,
) -> FieldComparison:
    for comparison in result["comparisons"]:
        if comparison["field_path"] == field_path:
            return comparison

    raise KeyError(f"No comparison found for field path: {field_path}")