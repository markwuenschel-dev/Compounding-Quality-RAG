from pathlib import Path

import pytest

from app.retrieval import (
    ChunkRecord,
    KeywordRetriever,
    load_chunks,
    retrieve,
    retrieve_from_chunks,
    tokenize,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "index" / "chunks.jsonl"


def test_chunks_index_exists() -> None:
    assert CHUNKS_PATH.exists(), f"Chunks index does not exist: {CHUNKS_PATH}"


def test_load_chunks_returns_chunk_records() -> None:
    chunks = load_chunks(CHUNKS_PATH)

    assert chunks
    assert chunks[0]["chunk_id"]
    assert chunks[0]["source_id"]
    assert chunks[0]["source_type"] == "sop"
    assert chunks[0]["text"]


def test_tokenize_removes_common_stop_words() -> None:
    terms = tokenize("What should happen for the flavored oral liquid?")

    assert "what" not in terms
    assert "should" not in terms
    assert "the" not in terms
    assert "flavored" in terms
    assert "oral" in terms
    assert "liquid" in terms


@pytest.mark.parametrize(
    ("query", "expected_source_ids"),
    [
        (
            "pet refuses flavored oral liquid palatability flavor concern",
            {"SOP-001", "SOP-004", "SOP-006"},
        ),
        (
            "customer reports vomiting after administration suspected adverse event",
            {"SOP-005", "SOP-007"},
        ),
        (
            "frontline pharmacist asks whether product is within beyond use date BUD",
            {"SOP-002", "SOP-005"},
        ),
        (
            "transdermal pen leaking air bubbles does not dispense after clicks",
            {"SOP-003", "SOP-006"},
        ),
        (
            "possible wrong patient wrong medication dispensing error",
            {"SOP-001", "SOP-007"},
        ),
    ],
)
def test_retrieve_returns_expected_source_in_top_five(
    query: str,
    expected_source_ids: set[str],
) -> None:
    results = retrieve(query, chunks_path=CHUNKS_PATH, top_k=5)

    actual_source_ids = {result["chunk"]["source_id"] for result in results}

    assert actual_source_ids & expected_source_ids, (
        f"Expected at least one of {sorted(expected_source_ids)} "
        f"but got {sorted(actual_source_ids)}"
    )


def test_retrieve_orders_results_by_score_descending() -> None:
    results = retrieve(
        "wrong patient wrong medication dispensing error",
        chunks_path=CHUNKS_PATH,
        top_k=5,
    )

    scores = [result["score"] for result in results]

    assert scores == sorted(scores, reverse=True)


def test_retrieve_respects_top_k() -> None:
    results = retrieve(
        "flavor refusal oral liquid palatability",
        chunks_path=CHUNKS_PATH,
        top_k=3,
    )

    assert len(results) <= 3


def test_retrieve_includes_matched_terms() -> None:
    results = retrieve(
        "transdermal pen leaking air bubbles",
        chunks_path=CHUNKS_PATH,
        top_k=1,
    )

    assert results
    assert results[0]["matched_terms"]


def test_retrieve_rejects_empty_query() -> None:
    with pytest.raises(ValueError, match="searchable term"):
        retrieve("   ", chunks_path=CHUNKS_PATH)


def test_retrieve_rejects_invalid_top_k() -> None:
    with pytest.raises(ValueError, match="top_k"):
        retrieve("flavor refusal", chunks_path=CHUNKS_PATH, top_k=0)


def test_retrieve_from_chunks_can_filter_by_source_type() -> None:
    chunks = sample_chunks()

    results = retrieve_from_chunks(
        query="flavor refusal",
        chunks=chunks,
        source_type="sop",
    )

    assert len(results) == 1
    assert results[0]["chunk"]["source_id"] == "SOP-TEST-001"


def test_keyword_retriever_matches_retrieve_from_chunks() -> None:
    chunks = load_chunks(CHUNKS_PATH)
    retriever = KeywordRetriever(chunks)

    direct_results = retrieve_from_chunks(
        query="flavor refusal oral liquid palatability",
        chunks=chunks,
        top_k=5,
        source_type="sop",
    )
    retriever_results = retriever.search(
        query="flavor refusal oral liquid palatability",
        top_k=5,
        source_type="sop",
    )

    assert retriever_results == direct_results


def test_keyword_retriever_respects_top_k() -> None:
    chunks = load_chunks(CHUNKS_PATH)
    retriever = KeywordRetriever(chunks)

    results = retriever.search(
        query="flavor refusal oral liquid palatability",
        top_k=2,
        source_type="sop",
    )

    assert len(results) <= 2


def test_keyword_retriever_can_filter_by_source_type() -> None:
    retriever = KeywordRetriever(sample_chunks())

    results = retriever.search(
        query="flavor refusal",
        source_type="synthetic_inquiry",
    )

    assert len(results) == 1
    assert results[0]["chunk"]["source_id"] == "INQ-TEST-001"


def test_seeded_debug_bug_keyword_retriever_filter_expectation() -> None:
    retriever = KeywordRetriever(sample_chunks())

    results = retriever.search(
        query="flavor refusal",
        source_type="sop",
    )

    # SEEDED DEBUG BUG: this assertion is intentionally wrong.
    assert results[0]["chunk"]["source_id"] == "SOP-TEST-001"


def sample_chunks() -> list[ChunkRecord]:
    return [
        {
            "chunk_id": "SOP-TEST-001::purpose",
            "source_id": "SOP-TEST-001",
            "source_file": "sop_test.md",
            "source_title": "Test SOP",
            "source_type": "sop",
            "section_heading": "Purpose",
            "process_area": "compounding_quality",
            "version": "1.0",
            "effective_date": "2025-01-01",
            "synthetic": True,
            "text": "Flavor refusal guidance.",
        },
        {
            "chunk_id": "INQ-TEST-001::raw-intake",
            "source_id": "INQ-TEST-001",
            "source_file": "inquiry_test.json",
            "source_title": "Test Inquiry",
            "source_type": "synthetic_inquiry",
            "section_heading": "Raw Intake",
            "process_area": "compounding_quality",
            "version": "1.0",
            "effective_date": "2025-01-01",
            "synthetic": True,
            "text": "Flavor refusal example.",
        },
    ]