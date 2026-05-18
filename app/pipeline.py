from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from app.retrieval import DEFAULT_CHUNKS_PATH, SearchResult, retrieve
from app.schemas import ExpectedStructuredOutput, SourceType

# run_stubbed_pipeline(...)
# run_stubbed_pipeline_for_file_name(...)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPECTED_OUTPUTS_DIR = PROJECT_ROOT / "data" / "expected_outputs"

class PipelineResult(TypedDict):
    inquiry_id: str
    inquiry_text: str
    retrieved_chunks: list[SearchResult]
    structured_output: ExpectedStructuredOutput

def run_stubbed_pipeline(expected_output_path: Path, *, chunks_path: Path = DEFAULT_CHUNKS_PATH, top_k: int = 5,) ->  PipelineResult:
    # 1. Check that the expected output file exists.
    # 2. Read the JSON file.
    # 3. Validate it as ExpectedStructuredOutput.
    # 4. Pull the inquiry text from raw_intake.concern_narrative.
    # 5. Retrieve SOP chunks using that inquiry text.
    # 6. Return all pieces in a PipelineResult dictionary.
    if not expected_output_path.exists():
        raise FileNotFoundError(f"Expected output file does not exist: {expected_output_path}")
    
    json_text = expected_output_path.read_text(encoding="utf-8")

    structured_output = ExpectedStructuredOutput.model_validate_json(json_text)
    
    inquiry_text = structured_output.raw_intake.concern_narrative

    retrieved_chunks = retrieve(query=inquiry_text, chunks_path=chunks_path, top_k=top_k, source_type=SourceType.SOP.value)

    return {"inquiry_id": expected_output_path.stem, "inquiry_text": inquiry_text, "retrieved_chunks": retrieved_chunks, "structured_output": structured_output}

def run_stubbed_pipeline_for_file_name(file_name: str, *, expected_output_dir: Path = DEFAULT_EXPECTED_OUTPUTS_DIR, chunks_path: Path = DEFAULT_CHUNKS_PATH, top_k: int = 5,) -> PipelineResult:
    expected_output_path = expected_output_dir / file_name

    return run_stubbed_pipeline(expected_output_path, chunks_path = chunks_path, top_k = top_k) 