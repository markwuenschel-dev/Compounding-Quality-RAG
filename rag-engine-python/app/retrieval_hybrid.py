from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import TypedDict

from app.retrieval import (
    DEFAULT_CHUNKS_PATH,
    ChunkRecord,
    SearchResult,
    chunk_text_for_scoring,
    load_chunks,
    score_chunk,
    tokenize,
)
from app.retrieval_embedding import (
    EmbeddingModel,
    HashingEmbeddingModel,
    cosine_similarity,
    matched_terms_for_embedding_result,
)


class HybridWeights(TypedDict):
    keyword: float
    embedding: float


class HybridCandidate(TypedDict):
    chunk: ChunkRecord
    keyword_score: float
    embedding_score: float
    normalized_keyword_score: float
    normalized_embedding_score: float
    score: float
    matched_terms: list[str]


class HybridRetriever:
    def __init__(
        self,
        chunks: list[ChunkRecord],
        embedding_model: EmbeddingModel,
        *,
        keyword_weight: float = 0.65,
        embedding_weight: float = 0.35,
    ) -> None:
        validate_hybrid_weights(
            keyword_weight=keyword_weight,
            embedding_weight=embedding_weight,
        )

        self._chunks = chunks
        self._embedding_model = embedding_model
        self._weights = normalize_hybrid_weights(
            keyword_weight=keyword_weight,
            embedding_weight=embedding_weight,
        )
        self._chunk_vectors = [
            embedding_model.embed_text(chunk_text_for_scoring(chunk))
            for chunk in chunks
        ]

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        source_type: str | None = None,
    ) -> list[SearchResult]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")

        query_terms = tokenize(query)

        if not query_terms:
            raise ValueError("query must contain at least one searchable term")

        candidates = self.score_candidates(
            query=query,
            source_type=source_type,
        )

        return [
            {
                "chunk": candidate["chunk"],
                "score": candidate["score"],
                "matched_terms": candidate["matched_terms"],
            }
            for candidate in sorted(
                candidates,
                key=lambda candidate: (
                    -candidate["score"],
                    candidate["chunk"]["chunk_id"],
                ),
            )[:top_k]
        ]

    def score_candidates(
        self,
        *,
        query: str,
        source_type: str | None = None,
    ) -> list[HybridCandidate]:
            query_terms = tokenize(query)

            if not query_terms:
                raise ValueError("query must contain at least one searchable term")

            query_term_counts = Counter(query_terms)
            query_vector = self._embedding_model.embed_text(query)

            raw_candidates: list[HybridCandidate] = []

            for chunk, chunk_vector in zip(self._chunks, self._chunk_vectors, strict=True):
                if source_type is not None and chunk["source_type"] != source_type:
                    continue

                keyword_score, keyword_matched_terms = score_chunk(query_term_counts, chunk)
                embedding_score = cosine_similarity(query_vector, chunk_vector)

                if keyword_score <= 0 and embedding_score <= 0:
                    continue

                embedding_matched_terms = matched_terms_for_embedding_result(
                    query=query,
                    chunk=chunk,
                )

                raw_candidates.append(
                    {
                        "chunk": chunk,
                        "keyword_score": keyword_score,
                        "embedding_score": embedding_score,
                        "normalized_keyword_score": 0.0,
                        "normalized_embedding_score": 0.0,
                        "score": 0.0,
                        "matched_terms": sorted(
                            set(keyword_matched_terms) | set(embedding_matched_terms)
                        ),
                    }
                )

            return score_hybrid_candidates(
                raw_candidates,
                weights=self._weights,
            )


def build_hybrid_retriever(
    *,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    embedding_dimensions: int = 128,
    keyword_weight: float = 0.65,
    embedding_weight: float = 0.35,
) -> HybridRetriever:
    return HybridRetriever(
        chunks=load_chunks(chunks_path),
        embedding_model=HashingEmbeddingModel(dimensions=embedding_dimensions),
        keyword_weight=keyword_weight,
        embedding_weight=embedding_weight,
    )


def score_hybrid_candidates(
    candidates: list[HybridCandidate],
    *,
    weights: HybridWeights,
) -> list[HybridCandidate]:
    max_keyword_score = max(
        (candidate["keyword_score"] for candidate in candidates),
        default=0.0,
    )
    max_embedding_score = max(
        (candidate["embedding_score"] for candidate in candidates),
        default=0.0,
    )

    scored_candidates: list[HybridCandidate] = []

    for candidate in candidates:
        normalized_keyword_score = normalize_score(
            candidate["keyword_score"],
            max_score=max_keyword_score,
        )
        normalized_embedding_score = normalize_score(
            candidate["embedding_score"],
            max_score=max_embedding_score,
        )

        hybrid_score = (
            weights["keyword"] * normalized_keyword_score
            + weights["embedding"] * normalized_embedding_score
        )

        scored_candidate: HybridCandidate = {
            "chunk": candidate["chunk"],
            "keyword_score": candidate["keyword_score"],
            "embedding_score": candidate["embedding_score"],
            "normalized_keyword_score": normalized_keyword_score,
            "normalized_embedding_score": normalized_embedding_score,
            "score": hybrid_score,
            "matched_terms": candidate["matched_terms"],
        }
        scored_candidates.append(scored_candidate)

    return scored_candidates


def normalize_score(score: float, *, max_score: float) -> float:
    if max_score <= 0:
        return 0.0

    return score / max_score


def validate_hybrid_weights(
    *,
    keyword_weight: float,
    embedding_weight: float,
) -> None:
    if keyword_weight < 0:
        raise ValueError("keyword_weight must be non-negative")

    if embedding_weight < 0:
        raise ValueError("embedding_weight must be non-negative")

    if keyword_weight == 0 and embedding_weight == 0:
        raise ValueError("at least one hybrid weight must be greater than zero")


def normalize_hybrid_weights(
    *,
    keyword_weight: float,
    embedding_weight: float,
) -> HybridWeights:
    validate_hybrid_weights(
        keyword_weight=keyword_weight,
        embedding_weight=embedding_weight,
    )

    total_weight = keyword_weight + embedding_weight

    return {
        "keyword": keyword_weight / total_weight,
        "embedding": embedding_weight / total_weight,
    }