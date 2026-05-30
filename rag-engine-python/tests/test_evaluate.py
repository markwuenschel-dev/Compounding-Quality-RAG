from pathlib import Path

import pytest

from app.evaluate import (
    DEFAULT_EXACT_MATCH_FIELD_PATHS,
    evaluate_structured_output,
    get_comparison,
    get_field_value,
    load_expected_output,
    normalize_for_comparison,
    
)

from app.schemas import ConcernType, ExpectedStructuredOutput, RiskLane
from tests.test_helpers import load_expected_output_normalized, write_normalized_expected_output


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_OUTPUTS_DIR = PROJECT_ROOT / "data" / "expected_outputs"


def load_flavor_refusal_output() -> ExpectedStructuredOutput:
    return load_expected_output_normalized(
        EXPECTED_OUTPUTS_DIR / "inquiry_001_flavor_refusal.json"
    )


def test_load_expected_output_returns_expected_structured_output(tmp_path: Path) -> None:
    normalized_path = write_normalized_expected_output(
        EXPECTED_OUTPUTS_DIR / "inquiry_001_flavor_refusal.json",
        tmp_path,
    )

    output = load_expected_output(normalized_path)

    assert isinstance(output, ExpectedStructuredOutput)
    assert output.derived_assessment.concern_type == ConcernType.PET_REFUSED_FLAVOR


def test_load_expected_output_rejects_missing_file(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError, match="Expected output file does not exist"):
        load_expected_output(missing_file)


def test_identical_structured_output_passes_evaluation() -> None:
    expected = load_flavor_refusal_output()
    actual = expected.model_copy(deep=True)

    result = evaluate_structured_output(expected=expected, actual=actual)

    assert result["passed"] is True
    assert result["failed_fields"] == []
    assert len(result["comparisons"]) == len(DEFAULT_EXACT_MATCH_FIELD_PATHS)
    assert all(comparison["passed"] for comparison in result["comparisons"])


def test_wrong_concern_type_fails_evaluation_and_reports_field() -> None:
    expected = load_flavor_refusal_output()
    actual = expected.model_copy(deep=True)
    actual.derived_assessment.concern_type = ConcernType.EFFICACY_CONCERN

    result = evaluate_structured_output(expected=expected, actual=actual)

    assert result["passed"] is False
    assert "derived_assessment.concern_type" in result["failed_fields"]

    comparison = get_comparison(result, "derived_assessment.concern_type")

    assert comparison["passed"] is False
    assert comparison["expected"] == "pet_refused_flavor"
    assert comparison["actual"] == "efficacy_concern"


def test_wrong_risk_lane_fails_evaluation_and_reports_field() -> None:
    expected = load_flavor_refusal_output()
    actual = expected.model_copy(deep=True)
    actual.derived_assessment.risk_lane = RiskLane.LIFE_THREATENING_OR_LEGAL

    result = evaluate_structured_output(expected=expected, actual=actual)

    assert result["passed"] is False
    assert "derived_assessment.risk_lane" in result["failed_fields"]

    comparison = get_comparison(result, "derived_assessment.risk_lane")

    assert comparison["expected"] == "expected_self_limiting"
    assert comparison["actual"] == "life_threatening_or_legal"


def test_rationale_is_not_exact_matched_by_default() -> None:
    expected = load_flavor_refusal_output()
    actual = expected.model_copy(deep=True)
    actual.derived_assessment.rationale = "Different wording with the same structured fields."

    result = evaluate_structured_output(expected=expected, actual=actual)

    assert result["passed"] is True
    assert "derived_assessment.rationale" not in result["failed_fields"]


def test_custom_field_paths_can_include_rationale() -> None:
    expected = load_flavor_refusal_output()
    actual = expected.model_copy(deep=True)
    actual.derived_assessment.rationale = "Different rationale."

    result = evaluate_structured_output(
        expected=expected,
        actual=actual,
        field_paths=("derived_assessment.rationale",),
    )

    assert result["passed"] is False
    assert result["failed_fields"] == ["derived_assessment.rationale"]


def test_get_field_value_reads_nested_model_field() -> None:
    output = load_flavor_refusal_output()

    value = get_field_value(output, "derived_assessment.concern_type")

    assert value == ConcernType.PET_REFUSED_FLAVOR


def test_get_field_value_rejects_invalid_path() -> None:
    output = load_flavor_refusal_output()

    with pytest.raises(AttributeError, match="Field path"):
        get_field_value(output, "derived_assessment.not_a_real_field")


def test_normalize_for_comparison_converts_enums_to_values() -> None:
    value = normalize_for_comparison(ConcernType.PET_REFUSED_FLAVOR)

    assert value == "pet_refused_flavor"


def test_normalize_for_comparison_converts_enum_lists_to_values() -> None:
    value = normalize_for_comparison(
        [
            ConcernType.PET_REFUSED_FLAVOR,
            ConcernType.EFFICACY_CONCERN,
        ]
    )

    assert value == [
        "pet_refused_flavor",
        "efficacy_concern",
    ]


def test_get_comparison_rejects_missing_field_path() -> None:
    expected = load_flavor_refusal_output()
    actual = expected.model_copy(deep=True)

    result = evaluate_structured_output(expected=expected, actual=actual)

    with pytest.raises(KeyError, match="No comparison found"):
        get_comparison(result, "derived_assessment.not_compared")