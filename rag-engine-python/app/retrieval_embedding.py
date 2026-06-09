from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Protocol

from app.retrieval import (
    DEFAULT_CHUNKS_PATH,
    ChunkRecord,
    SearchResult,
    chunk_text_for_scoring,
    load_chunks,
    tokenize,
)


class EmbeddingModel(Protocol):
    def embed_text(self, text: str) -> list[float]:
        ...


class HashingEmbeddingModel:
    def __init__(self, *, dimensions: int = 128) -> None:
        if dimensions < 1:
            raise ValueError("dimensions must be at least 1")

        self.dimensions = dimensions

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions

        for token in tokenize(text):
            index = stable_hash_index(token, self.dimensions)
            vector[index] += 1.0

        return normalize_vector(vector)


class EmbeddingRetriever:
    def __init__(
        self,
        chunks: list[ChunkRecord],
        embedding_model: EmbeddingModel,
    ) -> None:
        self._chunks = chunks
        self._embedding_model = embedding_model
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

        query_vector = self._embedding_model.embed_text(query)
        scored_results: list[SearchResult] = []

        for chunk, chunk_vector in zip(self._chunks, self._chunk_vectors, strict=True):
            if source_type is not None and chunk["source_type"] != source_type:
                continue

            score = cosine_similarity(query_vector, chunk_vector)

            if score <= 0:
                continue

            scored_results.append(
                {
                    "chunk": chunk,
                    "score": score,
                    "matched_terms": matched_terms_for_embedding_result(
                        query=query,
                        chunk=chunk,
                    ),
                }
            )

        return sorted(
            scored_results,
            key=lambda result: (-result["score"], result["chunk"]["chunk_id"]),
        )[:top_k]


def build_embedding_retriever(
    *,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    dimensions: int = 128,
) -> EmbeddingRetriever:
    return EmbeddingRetriever(
        chunks=load_chunks(chunks_path),
        embedding_model=HashingEmbeddingModel(dimensions=dimensions),
    )


def matched_terms_for_embedding_result(
    *,
    query: str,
    chunk: ChunkRecord,
) -> list[str]:
    query_terms = set(tokenize(query))
    chunk_terms = set(tokenize(chunk_text_for_scoring(chunk)))

    return sorted(query_terms & chunk_terms)


def stable_hash_index(value: str, dimensions: int) -> int:
    digest = hashlib.blake2b(value.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, byteorder="big", signed=False) % dimensions


def normalize_vector(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))

    if magnitude == 0:
        return vector

    return [value / magnitude for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have the same dimensions")

    left_magnitude = math.sqrt(sum(value * value for value in left))
    right_magnitude = math.sqrt(sum(value * value for value in right))

    if left_magnitude == 0 or right_magnitude == 0:
        return 0.0

    dot_product = sum(
        left_value * right_value
        for left_value, right_value in zip(left, right, strict=True)
    )

    return dot_product / (left_magnitude * right_magnitude)