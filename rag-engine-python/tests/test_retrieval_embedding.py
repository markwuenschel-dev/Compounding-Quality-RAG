from __future__ import annotations

from pathlib import Path

import pytest

from app.retrieval import ChunkRecord
from app.retrieval_embedding import (
    EmbeddingRetriever,
    HashingEmbeddingModel,
    build_embedding_retriever,
    cosine_similarity,
    matched_terms_for_embedding_result,
    normalize_vector,
    stable_hash_index,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "index" / "chunks.jsonl"


def test_hashing_embedding_model_returns_configured_dimensions() -> None:
    model = HashingEmbeddingModel(dimensions=16)

    vector = model.embed_text("flavor refusal oral liquid")

    assert len(vector) == 16


def test_hashing_embedding_model_rejects_invalid_dimensions() -> None:
    with pytest.raises(ValueError, match="dimensions"):
        HashingEmbeddingModel(dimensions=0)


def test_hashing_embedding_model_is_deterministic() -> None:
    model = HashingEmbeddingModel(dimensions=32)

    first = model.embed_text("flavor refusal oral liquid")
    second = model.embed_text("flavor refusal oral liquid")

    assert first == second


def test_hashing_embedding_model_normalizes_non_empty_vectors() -> None:
    model = HashingEmbeddingModel(dimensions=32)

    vector = model.embed_text("flavor refusal oral liquid")
    magnitude = sum(value * value for value in vector) ** 0.5

    assert magnitude == pytest.approx(1.0)


def test_hashing_embedding_model_preserves_repeated_term_strength() -> None:
    model = HashingEmbeddingModel(dimensions=32)

    single_term = model.embed_text("flavor")
    repeated_term = model.embed_text("flavor flavor flavor")

    assert cosine_similarity(single_term, repeated_term) == pytest.approx(1.0)


def test_stable_hash_index_stays_within_dimensions() -> None:
    for dimensions in [1, 2, 8, 128]:
        index = stable_hash_index("flavor", dimensions)

        assert 0 <= index < dimensions


def test_normalize_vector_returns_zero_vector_unchanged() -> None:
    assert normalize_vector([0.0, 0.0, 0.0]) == [0.0, 0.0, 0.0]


def test_normalize_vector_scales_nonzero_vector() -> None:
    vector = normalize_vector([3.0, 4.0])

    assert vector == pytest.approx([0.6, 0.8])


def test_cosine_similarity_returns_one_for_same_direction() -> None:
    assert cosine_similarity([1.0, 0.0], [2.0, 0.0]) == pytest.approx(1.0)


def test_cosine_similarity_returns_zero_for_orthogonal_vectors() -> None:
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_returns_zero_for_zero_vector() -> None:
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == pytest.approx(0.0)


def test_cosine_similarity_rejects_different_dimensions() -> None:
    with pytest.raises(ValueError, match="same dimensions"):
        cosine_similarity([1.0, 0.0], [1.0])


def test_embedding_retriever_returns_search_result_shape() -> None:
    retriever = EmbeddingRetriever(
        chunks=sample_chunks(),
        embedding_model=HashingEmbeddingModel(dimensions=64),
    )

    results = retriever.search("flavor refusal", top_k=1, source_type="sop")

    assert results
    assert set(results[0].keys()) == {"chunk", "score", "matched_terms"}
    assert results[0]["chunk"]["source_id"] == "SOP-FLAVOR"
    assert isinstance(results[0]["score"], float)
    assert results[0]["matched_terms"]


def test_embedding_retriever_respects_top_k() -> None:
    retriever = EmbeddingRetriever(
        chunks=sample_chunks(),
        embedding_model=HashingEmbeddingModel(dimensions=64),
    )

    results = retriever.search("flavor refusal quality review", top_k=2)

    assert len(results) <= 2


def test_embedding_retriever_rejects_invalid_top_k() -> None:
    retriever = EmbeddingRetriever(
        chunks=sample_chunks(),
        embedding_model=HashingEmbeddingModel(dimensions=64),
    )

    with pytest.raises(ValueError, match="top_k"):
        retriever.search("flavor refusal", top_k=0)


def test_embedding_retriever_rejects_blank_query() -> None:
    retriever = EmbeddingRetriever(
        chunks=sample_chunks(),
        embedding_model=HashingEmbeddingModel(dimensions=64),
    )

    with pytest.raises(ValueError, match="searchable term"):
        retriever.search("   ")


def test_embedding_retriever_filters_by_source_type() -> None:
    retriever = EmbeddingRetriever(
        chunks=sample_chunks(),
        embedding_model=HashingEmbeddingModel(dimensions=64),
    )

    results = retriever.search(
        "flavor refusal",
        top_k=5,
        source_type="synthetic_inquiry",
    )

    assert len(results) == 1
    assert results[0]["chunk"]["source_id"] == "INQ-FLAVOR"


def test_embedding_retriever_orders_by_similarity_descending() -> None:
    retriever = EmbeddingRetriever(
        chunks=sample_chunks(),
        embedding_model=HashingEmbeddingModel(dimensions=128),
    )

    results = retriever.search("transdermal pen leaking air bubbles", top_k=3)

    assert results[0]["chunk"]["source_id"] == "SOP-DEVICE"


def test_embedding_retriever_uses_stable_chunk_id_tiebreaker() -> None:
    chunks = [
        make_chunk(
            chunk_id="SOP-TIE-002::section",
            source_id="SOP-TIE-002",
            source_type="sop",
            text="Flavor refusal guidance.",
        ),
        make_chunk(
            chunk_id="SOP-TIE-001::section",
            source_id="SOP-TIE-001",
            source_type="sop",
            text="Flavor refusal guidance.",
        ),
    ]
    retriever = EmbeddingRetriever(
        chunks=chunks,
        embedding_model=HashingEmbeddingModel(dimensions=64),
    )

    results = retriever.search("flavor refusal", top_k=2)

    assert [result["chunk"]["chunk_id"] for result in results] == [
        "SOP-TIE-001::section",
        "SOP-TIE-002::section",
    ]


def test_embedding_retriever_finds_synonym_without_keyword_overlap() -> None:
    chunks = [
        make_chunk(
            chunk_id="SOP-VOMITING::section",
            source_id="SOP-VOMITING",
            source_type="sop",
            text="Vomiting after administration requires adverse event review.",
        ),
        make_chunk(
            chunk_id="SOP-DOSE::section",
            source_id="SOP-DOSE",
            source_type="sop",
            text="Dose field review requires checking the submitted quantity.",
        ),
    ]
    retriever = EmbeddingRetriever(
        chunks=chunks,
        embedding_model=HashingEmbeddingModel(dimensions=128),
    )

    results = retriever.search("emesis following dose", top_k=1, source_type="sop")

    assert results[0]["chunk"]["source_id"] == "SOP-DOSE"


def test_matched_terms_for_embedding_result_returns_lexical_overlap() -> None:
    chunk = make_chunk(
        chunk_id="SOP-FLAVOR::section",
        source_id="SOP-FLAVOR",
        source_type="sop",
        text="Flavor refusal guidance for oral liquid palatability.",
    )

    matched_terms = matched_terms_for_embedding_result(
        query="flavor refusal BUD",
        chunk=chunk,
    )

    assert matched_terms == ["flavor", "refusal"]


def test_build_embedding_retriever_runs_against_real_chunks() -> None:
    retriever = build_embedding_retriever(
        chunks_path=CHUNKS_PATH,
        dimensions=128,
    )

    results = retriever.search(
        "vomiting after flavored oral liquid",
        top_k=3,
        source_type="sop",
    )

    assert len(results) <= 3
    assert results


def sample_chunks() -> list[ChunkRecord]:
    return [
        make_chunk(
            chunk_id="SOP-FLAVOR::section",
            source_id="SOP-FLAVOR",
            source_type="sop",
            text="Flavor refusal guidance for oral liquid palatability concerns.",
        ),
        make_chunk(
            chunk_id="SOP-DEVICE::section",
            source_id="SOP-DEVICE",
            source_type="sop",
            text="Transdermal pen leaking air bubbles and click failure guidance.",
        ),
        make_chunk(
            chunk_id="INQ-FLAVOR::raw-intake",
            source_id="INQ-FLAVOR",
            source_type="synthetic_inquiry",
            text="Customer reported flavor refusal example.",
        ),
    ]


def make_chunk(
    *,
    chunk_id: str,
    source_id: str,
    source_type: str,
    text: str,
) -> ChunkRecord:
    return {
        "chunk_id": chunk_id,
        "source_id": source_id,
        "source_file": f"{source_id.lower()}.md",
        "source_title": f"{source_id} Title",
        "source_type": source_type,
        "section_heading": "Section",
        "process_area": "compounding_quality",
        "version": "1.0",
        "effective_date": "2025-01-01",
        "synthetic": True,
        "text": text,
    }