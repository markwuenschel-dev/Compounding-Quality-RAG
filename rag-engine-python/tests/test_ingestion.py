import json
from pathlib import Path

import pytest

from app.ingestion import (
    ingest_corpus,
    load_corpus_chunks,
    load_sop_document,
    split_sop_into_chunks,
    write_chunks_jsonl,
)
from app.schemas import SopDocument, SourceType


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = PROJECT_ROOT / "data" / "corpus"

EXPECTED_SOP_COUNT = 8

EXPECTED_DOCUMENT_IDS = {
    "SOP-001",
    "SOP-002",
    "SOP-003",
    "SOP-004",
    "SOP-005",
    "SOP-006",
    "SOP-007",
    "SOP-008",
}

REQUIRED_CHUNK_KEYS = {
    "chunk_id",
    "source_id",
    "source_file",
    "source_title",
    "source_type",
    "section_heading",
    "process_area",
    "version",
    "effective_date",
    "synthetic",
    "text",
}


def get_sop_paths() -> list[Path]:
    return sorted(CORPUS_DIR.glob("SOP-*.md"))


def test_corpus_directory_exists() -> None:
    assert CORPUS_DIR.exists(), f"Corpus directory does not exist: {CORPUS_DIR}"


def test_expected_sop_files_are_present() -> None:
    sop_paths = get_sop_paths()

    assert len(sop_paths) == EXPECTED_SOP_COUNT

    actual_document_ids = {
        path.stem.split("_", maxsplit=1)[0] for path in sop_paths
    }

    assert actual_document_ids == EXPECTED_DOCUMENT_IDS


def test_all_sop_documents_load_with_expected_document_ids() -> None:
    documents = [load_sop_document(path) for path in get_sop_paths()]

    actual_document_ids = {document.document_id for document in documents}

    assert actual_document_ids == EXPECTED_DOCUMENT_IDS

    for document in documents:
        assert document.source_type == SourceType.SOP
        assert document.synthetic is True
        assert document.body_text


def test_load_sop_document_reads_frontmatter_and_body() -> None:
    source_path = next(CORPUS_DIR.glob("SOP-001_*.md"))

    document = load_sop_document(source_path)

    assert document.document_id == "SOP-001"
    assert document.source_type == SourceType.SOP
    assert document.synthetic is True
    assert document.body_text
    assert "Intake Classification" in document.title


def test_load_sop_document_rejects_missing_frontmatter(tmp_path: Path) -> None:
    invalid_sop = tmp_path / "invalid_sop.md"
    invalid_sop.write_text("# Invalid SOP\n\nNo frontmatter here.", encoding="utf-8")

    with pytest.raises(ValueError, match="frontmatter"):
        load_sop_document(invalid_sop)


def test_load_sop_document_rejects_missing_required_frontmatter_field(
    tmp_path: Path,
) -> None:
    invalid_sop = tmp_path / "invalid_sop.md"
    invalid_sop.write_text(
        """---
document_id: SOP-TEST-001
title: Test SOP
version: "1.0"
process_area: compounding_quality
source_type: sop
synthetic: true
---

# Test SOP

## Purpose

Test body.
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing frontmatter fields"):
        load_sop_document(invalid_sop)


def test_split_sop_into_chunks_uses_second_level_headings() -> None:
    document = SopDocument(
        document_id="SOP-TEST-001",
        title="Test SOP",
        version="1.0",
        effective_date="2025-01-01",
        process_area="compounding_quality",
        source_type=SourceType.SOP,
        synthetic=True,
        body_text="""# Test SOP

## Purpose

Purpose text.

## Handling Path Guidance

Handling path text.
""",
    )

    chunks = split_sop_into_chunks(document, Path("sop_test.md"))

    assert len(chunks) == 2

    assert chunks[0]["chunk_id"] == "SOP-TEST-001::purpose"
    assert chunks[0]["section_heading"] == "Purpose"
    assert chunks[0]["text"] == "Purpose\n\nPurpose text."

    assert chunks[1]["chunk_id"] == "SOP-TEST-001::handling-path-guidance"
    assert chunks[1]["section_heading"] == "Handling Path Guidance"
    assert chunks[1]["text"] == "Handling Path Guidance\n\nHandling path text."


def test_load_corpus_chunks_returns_non_empty_chunks() -> None:
    chunks = load_corpus_chunks(CORPUS_DIR)

    assert chunks


def test_corpus_chunks_have_required_metadata() -> None:
    chunks = load_corpus_chunks(CORPUS_DIR)

    for chunk in chunks:
        assert REQUIRED_CHUNK_KEYS <= chunk.keys()
        assert chunk["chunk_id"]
        assert chunk["source_id"]
        assert chunk["source_file"].endswith(".md")
        assert chunk["source_title"]
        assert chunk["source_type"] == "sop"
        assert chunk["section_heading"]
        assert chunk["process_area"]
        assert chunk["version"]
        assert chunk["effective_date"]
        assert chunk["synthetic"] is True
        assert chunk["text"]


def test_corpus_chunk_ids_are_unique() -> None:
    chunks = load_corpus_chunks(CORPUS_DIR)
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]

    assert len(chunk_ids) == len(set(chunk_ids))


def test_write_chunks_jsonl_writes_one_json_object_per_line(tmp_path: Path) -> None:
    chunks = load_corpus_chunks(CORPUS_DIR)[:3]
    output_path = tmp_path / "chunks.jsonl"

    write_chunks_jsonl(chunks, output_path)

    lines = output_path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == len(chunks)

    for line in lines:
        parsed = json.loads(line)
        assert REQUIRED_CHUNK_KEYS <= parsed.keys()


def test_ingest_corpus_writes_chunks_jsonl(tmp_path: Path) -> None:
    output_path = tmp_path / "chunks.jsonl"

    chunks = ingest_corpus(CORPUS_DIR, output_path)

    assert output_path.exists()

    lines = output_path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == len(chunks)
    assert len(chunks) > 0
