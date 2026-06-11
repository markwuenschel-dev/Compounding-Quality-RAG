from __future__ import annotations

import pytest

from app.retrieval import ChunkRecord
from app.retrieval_embedding import EmbeddingModel
from app.retrieval_hybrid import (
    HybridCandidate,
    HybridRetriever,
    build_hybrid_retriever,
    normalize_hybrid_weights,
    normalize_score,
    score_hybrid_candidates,
)


class RuleEmbeddingModel(EmbeddingModel):
    def embed_text(self, text: str) -> list[float]:
        normalized = text.lower()

        if "semantic-query" in normalized:
            return [1.0, 0.0, 0.0]

        if "embedding-match" in normalized:
            return [1.0, 0.0, 0.0]

        if "keyword-match" in normalized:
            return [0.0, 1.0, 0.0]

        if "device-match" in normalized:
            return [0.0, 0.0, 1.0]

        return [0.0, 0.0, 0.0]


def test_normalize_score_returns_zero_when_max_score_is_zero() -> None:
    assert normalize_score(10.0, max_score=0.0) == 0.0


def test_normalize_score_scales_against_max_score() -> None:
    assert normalize_score(2.5, max_score=10.0) == pytest.approx(0.25)


def test_normalize_hybrid_weights_scales_weights_to_sum_to_one() -> None:
    weights = normalize_hybrid_weights(keyword_weight=2.0, embedding_weight=1.0)

    assert weights["keyword"] == pytest.approx(2 / 3)
    assert weights["embedding"] == pytest.approx(1 / 3)


def test_normalize_hybrid_weights_rejects_negative_keyword_weight() -> None:
    with pytest.raises(ValueError, match="keyword_weight"):
        normalize_hybrid_weights(keyword_weight=-0.1, embedding_weight=1.0)


def test_normalize_hybrid_weights_rejects_negative_embedding_weight() -> None:
    with pytest.raises(ValueError, match="embedding_weight"):
        normalize_hybrid_weights(keyword_weight=1.0, embedding_weight=-0.1)


def test_normalize_hybrid_weights_rejects_all_zero_weights() -> None:
    with pytest.raises(ValueError, match="at least one"):
        normalize_hybrid_weights(keyword_weight=0.0, embedding_weight=0.0)


def test_score_hybrid_candidates_combines_normalized_component_scores() -> None:
    candidates: list[HybridCandidate] = [
        {
            "chunk": make_chunk(
                chunk_id="SOP-001::section",
                source_id="SOP-001",
                source_type="sop",
                text="Keyword only.",
            ),
            "keyword_score": 4.0,
            "embedding_score": 0.25,
            "normalized_keyword_score": 0.0,
            "normalized_embedding_score": 0.0,
            "score": 0.0,
            "matched_terms": ["keyword"],
        },
        {
            "chunk": make_chunk(
                chunk_id="SOP-002::section",
                source_id="SOP-002",
                source_type="sop",
                text="Embedding only.",
            ),
            "keyword_score": 2.0,
            "embedding_score": 1.0,
            "normalized_keyword_score": 0.0,
            "normalized_embedding_score": 0.0,
            "score": 0.0,
            "matched_terms": ["embedding"],
        },
    ]

    scored = score_hybrid_candidates(
        candidates,
        weights={"keyword": 0.5, "embedding": 0.5},
    )

    assert scored[0]["score"] == pytest.approx(0.625)
    assert scored[1]["score"] == pytest.approx(0.75)


def test_hybrid_retriever_returns_search_result_shape() -> None:
    retriever = HybridRetriever(
        chunks=sample_chunks(),
        embedding_model=RuleEmbeddingModel(),
    )

    results = retriever.search("flavor refusal semantic-query", top_k=1)

    assert results
    assert set(results[0].keys()) == {"chunk", "score", "matched_terms"}
    assert isinstance(results[0]["score"], float)
    assert isinstance(results[0]["matched_terms"], list)


def test_hybrid_retriever_respects_top_k() -> None:
    retriever = HybridRetriever(
        chunks=sample_chunks(),
        embedding_model=RuleEmbeddingModel(),
    )

    results = retriever.search("flavor refusal semantic-query", top_k=2)

    assert len(results) <= 2


def test_hybrid_retriever_rejects_invalid_top_k() -> None:
    retriever = HybridRetriever(
        chunks=sample_chunks(),
        embedding_model=RuleEmbeddingModel(),
    )

    with pytest.raises(ValueError, match="top_k"):
        retriever.search("flavor refusal", top_k=0)


def test_hybrid_retriever_rejects_blank_query() -> None:
    retriever = HybridRetriever(
        chunks=sample_chunks(),
        embedding_model=RuleEmbeddingModel(),
    )

    with pytest.raises(ValueError, match="searchable term"):
        retriever.search("   ")


def test_hybrid_retriever_filters_by_source_type() -> None:
    retriever = HybridRetriever(
        chunks=sample_chunks(),
        embedding_model=RuleEmbeddingModel(),
    )

    results = retriever.search(
        "flavor refusal semantic-query",
        top_k=5,
        source_type="synthetic_inquiry",
    )

    assert len(results) == 1
    assert results[0]["chunk"]["source_id"] == "INQ-FLAVOR"


def test_hybrid_retriever_uses_chunk_id_tiebreaker() -> None:
    chunks = [
        make_chunk(
            chunk_id="SOP-TIE-002::section",
            source_id="SOP-TIE-002",
            source_type="sop",
            text="Flavor refusal embedding-match.",
        ),
        make_chunk(
            chunk_id="SOP-TIE-001::section",
            source_id="SOP-TIE-001",
            source_type="sop",
            text="Flavor refusal embedding-match.",
        ),
    ]
    retriever = HybridRetriever(
        chunks=chunks,
        embedding_model=RuleEmbeddingModel(),
    )

    results = retriever.search("flavor refusal semantic-query", top_k=2)

    assert [result["chunk"]["chunk_id"] for result in results] == [
        "SOP-TIE-001::section",
        "SOP-TIE-002::section",
    ]


def test_hybrid_retriever_can_prioritize_embedding_signal() -> None:
    chunks = [
        make_chunk(
            chunk_id="SOP-KEYWORD::section",
            source_id="SOP-KEYWORD",
            source_type="sop",
            text="semantic-query semantic-query semantic-query keyword-match.",
        ),
        make_chunk(
            chunk_id="SOP-EMBEDDING::section",
            source_id="SOP-EMBEDDING",
            source_type="sop",
            text="embedding-match.",
        ),
    ]
    retriever = HybridRetriever(
        chunks=chunks,
        embedding_model=RuleEmbeddingModel(),
        keyword_weight=0.5,
        embedding_weight=0.5,
    )

    results = retriever.search("semantic-query", top_k=2)

    assert results[0]["chunk"]["source_id"] == "SOP-KEYWORD"


def test_hybrid_retriever_keyword_only_weight_ignores_embedding_signal() -> None:
    chunks = [
        make_chunk(
            chunk_id="SOP-KEYWORD::section",
            source_id="SOP-KEYWORD",
            source_type="sop",
            text="flavor refusal keyword-match.",
        ),
        make_chunk(
            chunk_id="SOP-EMBEDDING::section",
            source_id="SOP-EMBEDDING",
            source_type="sop",
            text="embedding-match.",
        ),
    ]
    retriever = HybridRetriever(
        chunks=chunks,
        embedding_model=RuleEmbeddingModel(),
        keyword_weight=1.0,
        embedding_weight=0.0,
    )

    results = retriever.search("flavor refusal semantic-query", top_k=2)

    assert results[0]["chunk"]["source_id"] == "SOP-KEYWORD"


def test_hybrid_retriever_embedding_only_weight_ignores_keyword_signal() -> None:
    chunks = [
        make_chunk(
            chunk_id="SOP-KEYWORD::section",
            source_id="SOP-KEYWORD",
            source_type="sop",
            text="semantic-query semantic-query keyword-match.",
        ),
        make_chunk(
            chunk_id="SOP-EMBEDDING::section",
            source_id="SOP-EMBEDDING",
            source_type="sop",
            text="embedding-match.",
        ),
    ]
    retriever = HybridRetriever(
        chunks=chunks,
        embedding_model=RuleEmbeddingModel(),
        keyword_weight=0.0,
        embedding_weight=1.0,
    )

    results = retriever.search("semantic-query", top_k=2)

    assert results[0]["chunk"]["source_id"] == "SOP-EMBEDDING"


def test_hybrid_score_candidates_exposes_component_scores_for_debugging() -> None:
    chunks = sample_chunks()
    retriever = HybridRetriever(
        chunks=chunks,
        embedding_model=RuleEmbeddingModel(),
    )

    candidates = retriever.score_candidates(
        query="flavor refusal semantic-query",
        source_type="sop",
    )

    assert candidates
    assert set(candidates[0].keys()) == {
        "chunk",
        "keyword_score",
        "embedding_score",
        "normalized_keyword_score",
        "normalized_embedding_score",
        "score",
        "matched_terms",
    }


def test_build_hybrid_retriever_runs_against_real_chunks() -> None:
    retriever = build_hybrid_retriever()

    results = retriever.search(
        "vomiting after flavored oral liquid",
        top_k=3,
        source_type="sop",
    )

    assert results
    assert len(results) <= 3


def sample_chunks() -> list[ChunkRecord]:
    return [
        make_chunk(
            chunk_id="SOP-FLAVOR::section",
            source_id="SOP-FLAVOR",
            source_type="sop",
            text="Flavor refusal guidance for oral liquid palatability embedding-match.",
        ),
        make_chunk(
            chunk_id="SOP-DEVICE::section",
            source_id="SOP-DEVICE",
            source_type="sop",
            text="Transdermal pen leaking air bubbles device-match.",
        ),
        make_chunk(
            chunk_id="INQ-FLAVOR::raw-intake",
            source_id="INQ-FLAVOR",
            source_type="synthetic_inquiry",
            text="Customer reported flavor refusal example embedding-match.",
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