from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Protocol, TypedDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHUNKS_PATH = PROJECT_ROOT / "data" / "index" / "chunks.jsonl"

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

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "if",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "that",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "whether",
    "with",
}


class ChunkRecord(TypedDict):
    chunk_id: str
    source_id: str
    source_file: str
    source_title: str
    source_type: str
    section_heading: str
    process_area: str
    version: str
    effective_date: str
    synthetic: bool
    text: str


class SearchResult(TypedDict):
    chunk: ChunkRecord
    score: float
    matched_terms: list[str]


class Retriever(Protocol):
    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        source_type: str | None = None,
    ) -> list[SearchResult]:
        ...


class KeywordRetriever:
    def __init__(self, chunks: list[ChunkRecord]) -> None:
        self._chunks = chunks

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        source_type: str | None = None,
    ) -> list[SearchResult]:
        return score_keyword_results(
            query=query,
            chunks=self._chunks,
            top_k=top_k,
            source_type=source_type,
        )


def load_chunks(chunks_path: Path = DEFAULT_CHUNKS_PATH) -> list[ChunkRecord]:
    if not chunks_path.exists():
        raise FileNotFoundError(f"Chunks file does not exist: {chunks_path}")

    chunks: list[ChunkRecord] = []

    for line_number, line in enumerate(
        chunks_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue

        try:
            raw_chunk = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"{chunks_path.name} line {line_number} is not valid JSON"
            ) from exc

        if not isinstance(raw_chunk, dict):
            raise ValueError(
                f"{chunks_path.name} line {line_number} must be a JSON object"
            )

        chunks.append(parse_chunk_record(raw_chunk, chunks_path, line_number))

    if not chunks:
        raise ValueError(f"No chunks found in {chunks_path}")

    return chunks


def parse_chunk_record(
    raw_chunk: dict[str, Any],
    chunks_path: Path,
    line_number: int,
) -> ChunkRecord:
    missing_keys = REQUIRED_CHUNK_KEYS - raw_chunk.keys()

    if missing_keys:
        raise ValueError(
            f"{chunks_path.name} line {line_number} is missing keys: "
            f"{sorted(missing_keys)}"
        )

    if not isinstance(raw_chunk["synthetic"], bool):
        raise ValueError(
            f"{chunks_path.name} line {line_number} field 'synthetic' must be boolean"
        )

    return {
        "chunk_id": str(raw_chunk["chunk_id"]),
        "source_id": str(raw_chunk["source_id"]),
        "source_file": str(raw_chunk["source_file"]),
        "source_title": str(raw_chunk["source_title"]),
        "source_type": str(raw_chunk["source_type"]),
        "section_heading": str(raw_chunk["section_heading"]),
        "process_area": str(raw_chunk["process_area"]),
        "version": str(raw_chunk["version"]),
        "effective_date": str(raw_chunk["effective_date"]),
        "synthetic": raw_chunk["synthetic"],
        "text": str(raw_chunk["text"]),
    }


def retrieve(
    query: str,
    *,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    top_k: int = 5,
    source_type: str | None = None,
) -> list[SearchResult]:
    chunks = load_chunks(chunks_path)
    retriever = KeywordRetriever(chunks)

    return retriever.search(
        query=query,
        top_k=top_k,
        source_type=source_type,
    )


def retrieve_from_chunks(
    query: str,
    chunks: list[ChunkRecord],
    *,
    top_k: int = 5,
    source_type: str | None = None,
) -> list[SearchResult]:
    retriever = KeywordRetriever(chunks)

    return retriever.search(
        query=query,
        top_k=top_k,
        source_type=source_type,
    )


def score_keyword_results(
    query: str,
    chunks: list[ChunkRecord],
    *,
    top_k: int = 5,
    source_type: str | None = None,
) -> list[SearchResult]:
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    query_terms = Counter(tokenize(query))

    if not query_terms:
        raise ValueError("query must contain at least one searchable term")

    scored_results: list[SearchResult] = []

    for chunk in chunks:
        if source_type is not None and chunk["source_type"] != source_type:
            continue

        score, matched_terms = score_chunk(query_terms, chunk)

        if score <= 0:
            continue

        scored_results.append(
            {
                "chunk": chunk,
                "score": score,
                "matched_terms": matched_terms,
            }
        )

    return sorted(
        scored_results,
        key=lambda result: (-result["score"], result["chunk"]["chunk_id"]),
    )[:top_k]


def score_chunk(
    query_terms: Counter[str],
    chunk: ChunkRecord,
) -> tuple[float, list[str]]:
    document_terms = Counter(tokenize(chunk_text_for_scoring(chunk)))
    title_terms = set(tokenize(chunk["source_title"]))
    heading_terms = set(tokenize(chunk["section_heading"]))

    score = 0.0
    matched_terms: list[str] = []

    for term, query_count in query_terms.items():
        document_count = document_terms.get(term, 0)

        if document_count == 0:
            continue

        matched_terms.append(term)

        score += query_count * min(document_count, 3)

        if term in title_terms:
            score += 2.0

        if term in heading_terms:
            score += 1.0

    return score, sorted(matched_terms)


def chunk_text_for_scoring(chunk: ChunkRecord) -> str:
    return " ".join(
        [
            chunk["source_title"],
            chunk["section_heading"],
            chunk["text"],
        ]
    )


def tokenize(text: str) -> list[str]:
    raw_terms = re.findall(r"[a-z0-9]+", text.lower())

    return [
        term
        for term in raw_terms
        if len(term) > 1 and term not in STOP_WORDS
    ]