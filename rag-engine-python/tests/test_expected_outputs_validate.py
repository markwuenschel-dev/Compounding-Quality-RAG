from pathlib import Path

import pytest

from app.schemas import ExpectedStructuredOutput
from tests.test_helpers import load_expected_output_normalized


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_OUTPUTS_DIR = PROJECT_ROOT / "data" / "expected_outputs"

EXPECTED_OUTPUT_FILE_NAMES = [
    "inquiry_001_flavor_refusal.json",
    "inquiry_002_flavor_related_vomiting.json",
    "inquiry_003_bud_question.json",
    "inquiry_004_transdermal_pen_issue.json",
    "inquiry_005_wrong_patient_wrong_medication.json",
]


def test_expected_outputs_directory_exists() -> None:
    assert EXPECTED_OUTPUTS_DIR.exists(), (
        f"Expected output directory does not exist: {EXPECTED_OUTPUTS_DIR}"
    )


def test_expected_output_files_are_present() -> None:
    json_paths = sorted(EXPECTED_OUTPUTS_DIR.glob("*.json"))
    actual_file_names = {path.name for path in json_paths}
    expected_file_names = set(EXPECTED_OUTPUT_FILE_NAMES)

    missing_files = expected_file_names - actual_file_names
    unexpected_files = actual_file_names - expected_file_names

    assert not missing_files, f"Missing expected output files: {sorted(missing_files)}"
    assert not unexpected_files, f"Unexpected expected output files: {sorted(unexpected_files)}"


@pytest.mark.parametrize("file_name", EXPECTED_OUTPUT_FILE_NAMES)
def test_expected_output_validates_against_schema(file_name: str) -> None:
    json_path = EXPECTED_OUTPUTS_DIR / file_name

    output = load_expected_output_normalized(json_path)

    assert isinstance(output, ExpectedStructuredOutput)


@pytest.mark.parametrize(
    "file_name",
    [
        "inquiry_001_flavor_refusal.json",
        "inquiry_002_flavor_related_vomiting.json",
        "inquiry_003_bud_question.json",
        "inquiry_004_transdermal_pen_issue.json",
    ],
)
def test_expected_output_uses_known_dosage_form_when_case_provides_it(
    file_name: str,
) -> None:
    json_path = EXPECTED_OUTPUTS_DIR / file_name

    output = load_expected_output_normalized(json_path)

    assert output.product_context.dosage_form.value != "unknown"