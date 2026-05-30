from pathlib import Path

import pytest

from app.pipeline import (
    DEFAULT_EXPECTED_OUTPUTS_DIR,
    run_stubbed_pipeline,
    run_stubbed_pipeline_for_file_name,
)
from app.schemas import ConcernType, ExpectedStructuredOutput, RiskLane
from tests.test_helpers import write_normalized_expected_outputs_dir


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "index" / "chunks.jsonl"

EXPECTED_OUTPUT_FILE_NAMES = [
    "inquiry_001_flavor_refusal.json",
    "inquiry_002_flavor_related_vomiting.json",
    "inquiry_003_bud_question.json",
    "inquiry_004_transdermal_pen_issue.json",
    "inquiry_005_wrong_patient_wrong_medication.json",
]


@pytest.fixture()
def normalized_expected_outputs_dir(tmp_path: Path) -> Path:
    return write_normalized_expected_outputs_dir(
        DEFAULT_EXPECTED_OUTPUTS_DIR,
        tmp_path / "expected_outputs",
    )


def test_stubbed_pipeline_runs_for_flavor_refusal(
    normalized_expected_outputs_dir: Path,
) -> None:
    result = run_stubbed_pipeline_for_file_name(
        "inquiry_001_flavor_refusal.json",
        expected_output_dir=normalized_expected_outputs_dir,
        chunks_path=CHUNKS_PATH,
    )

    assert result["inquiry_id"] == "inquiry_001_flavor_refusal"
    assert result["inquiry_text"]
    assert result["retrieved_chunks"]
    assert isinstance(result["structured_output"], ExpectedStructuredOutput)


def test_stubbed_pipeline_returns_expected_flavor_refusal_assessment(
    normalized_expected_outputs_dir: Path,
) -> None:
    result = run_stubbed_pipeline_for_file_name(
        "inquiry_001_flavor_refusal.json",
        expected_output_dir=normalized_expected_outputs_dir,
        chunks_path=CHUNKS_PATH,
    )

    structured_output = result["structured_output"]

    assert (
        structured_output.derived_assessment.concern_type
        == ConcernType.PET_REFUSED_FLAVOR
    )
    assert (
        structured_output.derived_assessment.risk_lane
        == RiskLane.EXPECTED_SELF_LIMITING
    )


@pytest.mark.parametrize("file_name", EXPECTED_OUTPUT_FILE_NAMES)
def test_stubbed_pipeline_runs_for_each_expected_output(
    file_name: str,
    normalized_expected_outputs_dir: Path,
) -> None:
    result = run_stubbed_pipeline_for_file_name(
        file_name,
        expected_output_dir=normalized_expected_outputs_dir,
        chunks_path=CHUNKS_PATH,
    )

    assert result["inquiry_id"] == Path(file_name).stem
    assert result["inquiry_text"]
    assert result["retrieved_chunks"]
    assert isinstance(result["structured_output"], ExpectedStructuredOutput)


@pytest.mark.parametrize("file_name", EXPECTED_OUTPUT_FILE_NAMES)
def test_stubbed_pipeline_retrieves_only_sop_chunks(
    file_name: str,
    normalized_expected_outputs_dir: Path,
) -> None:
    result = run_stubbed_pipeline_for_file_name(
        file_name,
        expected_output_dir=normalized_expected_outputs_dir,
        chunks_path=CHUNKS_PATH,
    )

    assert result["retrieved_chunks"]

    for search_result in result["retrieved_chunks"]:
        assert search_result["chunk"]["source_type"] == "sop"


@pytest.mark.parametrize("file_name", EXPECTED_OUTPUT_FILE_NAMES)
def test_stubbed_pipeline_retrieved_chunks_have_scores(
    file_name: str,
    normalized_expected_outputs_dir: Path,
) -> None:
    result = run_stubbed_pipeline_for_file_name(
        file_name,
        expected_output_dir=normalized_expected_outputs_dir,
        chunks_path=CHUNKS_PATH,
    )

    for search_result in result["retrieved_chunks"]:
        assert search_result["score"] > 0
        assert search_result["matched_terms"]


def test_stubbed_pipeline_respects_top_k(
    normalized_expected_outputs_dir: Path,
) -> None:
    result = run_stubbed_pipeline_for_file_name(
        "inquiry_001_flavor_refusal.json",
        expected_output_dir=normalized_expected_outputs_dir,
        chunks_path=CHUNKS_PATH,
        top_k=3,
    )

    assert len(result["retrieved_chunks"]) <= 3


def test_stubbed_pipeline_rejects_missing_expected_output(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing_expected_output.json"

    with pytest.raises(FileNotFoundError, match="Expected output file does not exist"):
        run_stubbed_pipeline(missing_file, chunks_path=CHUNKS_PATH)


def test_expected_outputs_dir_default_points_to_project_data() -> None:
    assert DEFAULT_EXPECTED_OUTPUTS_DIR.exists()
    assert DEFAULT_EXPECTED_OUTPUTS_DIR.name == "expected_outputs"