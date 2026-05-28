from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, TypedDict

from app.schemas import SopDocument


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS_DIR = PROJECT_ROOT / "data" / "corpus"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "index" / "chunks.jsonl"

REQUIRED_FRONTMATTER_FIELDS = {
    "document_id",
    "title",
    "version",
    "effective_date",
    "process_area",
    "source_type",
    "synthetic",
}


class SopChunk(TypedDict):
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


def parse_frontmatter(markdown_text: str, source_path: Path) -> tuple[dict[str, Any], str]:
    lines = markdown_text.splitlines()

    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{source_path.name} must start with a frontmatter block")

    closing_index = None

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        raise ValueError(f"{source_path.name} frontmatter block is not closed")

    metadata_lines = lines[1:closing_index]
    body_lines = lines[closing_index + 1 :]

    metadata = parse_metadata_lines(metadata_lines, source_path)
    body_text = "\n".join(body_lines).strip()

    if not body_text:
        raise ValueError(f"{source_path.name} has empty body text")

    missing_fields = REQUIRED_FRONTMATTER_FIELDS - metadata.keys()

    if missing_fields:
        raise ValueError(
            f"{source_path.name} is missing frontmatter fields: {sorted(missing_fields)}"
        )

    return metadata, body_text


def parse_metadata_lines(lines: list[str], source_path: Path) -> dict[str, Any]:
    metadata: dict[str, Any] = {}

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        if ":" not in stripped:
            raise ValueError(f"{source_path.name} has invalid frontmatter line: {line}")

        key, raw_value = stripped.split(":", maxsplit=1)
        metadata[key.strip()] = parse_metadata_value(raw_value.strip())

    return metadata


def parse_metadata_value(raw_value: str) -> str | bool:
    if raw_value.lower() == "true":
        return True

    if raw_value.lower() == "false":
        return False

    if (
        len(raw_value) >= 2
        and raw_value[0] == raw_value[-1]
        and raw_value[0] in {"'", '"'}
    ):
        return raw_value[1:-1]

    return raw_value


def load_sop_document(source_path: Path) -> SopDocument:
    markdown_text = source_path.read_text(encoding="utf-8")
    metadata, body_text = parse_frontmatter(markdown_text, source_path)

    return SopDocument(
        document_id=str(metadata["document_id"]),
        title=str(metadata["title"]),
        version=str(metadata["version"]),
        effective_date=str(metadata["effective_date"]),
        process_area=str(metadata["process_area"]),
        source_type=metadata["source_type"],
        synthetic=metadata["synthetic"],
        body_text=body_text,
    )


def split_sop_into_chunks(document: SopDocument, source_path: Path) -> list[SopChunk]:
    section_matches = list(re.finditer(r"^##\s+(.+?)\s*$", document.body_text, re.MULTILINE))

    if not section_matches:
        return [
            build_chunk(
                document=document,
                source_path=source_path,
                section_heading="Document",
                section_slug="document",
                text=document.body_text,
            )
        ]

    chunks: list[SopChunk] = []
    slug_counts: dict[str, int] = {}

    for index, match in enumerate(section_matches):
        section_heading = match.group(1).strip()
        section_start = match.end()
        section_end = (
            section_matches[index + 1].start()
            if index + 1 < len(section_matches)
            else len(document.body_text)
        )

        section_body = document.body_text[section_start:section_end].strip()

        if not section_body:
            continue

        base_slug = slugify(section_heading)
        slug_counts[base_slug] = slug_counts.get(base_slug, 0) + 1

        section_slug = (
            base_slug
            if slug_counts[base_slug] == 1
            else f"{base_slug}-{slug_counts[base_slug]}"
        )

        chunk_text = f"{section_heading}\n\n{section_body}"

        chunks.append(
            build_chunk(
                document=document,
                source_path=source_path,
                section_heading=section_heading,
                section_slug=section_slug,
                text=chunk_text,
            )
        )

    if not chunks:
        raise ValueError(f"{source_path.name} did not produce any non-empty chunks")

    return chunks


def build_chunk(
    document: SopDocument,
    source_path: Path,
    section_heading: str,
    section_slug: str,
    text: str,
) -> SopChunk:
    cleaned_text = normalize_text(text)

    if not cleaned_text:
        raise ValueError(
            f"{source_path.name} section {section_heading!r} produced empty text"
        )

    return {
        "chunk_id": f"{document.document_id}::{section_slug}",
        "source_id": document.document_id,
        "source_file": source_path.name,
        "source_title": document.title,
        "source_type": document.source_type.value,
        "section_heading": section_heading,
        "process_area": document.process_area,
        "version": document.version,
        "effective_date": document.effective_date,
        "synthetic": document.synthetic,
        "text": cleaned_text,
    }


def normalize_text(text: str) -> str:
    lines = [line.rstrip() for line in text.strip().splitlines()]
    return "\n".join(lines).strip()


def slugify(value: str) -> str:
    slug = value.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")

    if not slug:
        raise ValueError(f"Cannot create slug from heading: {value!r}")

    return slug


def load_corpus_chunks(corpus_dir: Path = DEFAULT_CORPUS_DIR) -> list[SopChunk]:
    if not corpus_dir.exists():
        raise FileNotFoundError(f"Corpus directory does not exist: {corpus_dir}")

    markdown_paths = sorted(corpus_dir.glob("*.md"))

    if not markdown_paths:
        raise FileNotFoundError(f"No markdown SOP files found in {corpus_dir}")

    chunks: list[SopChunk] = []

    for markdown_path in markdown_paths:
        document = load_sop_document(markdown_path)
        chunks.extend(split_sop_into_chunks(document, markdown_path))

    return chunks


def write_chunks_jsonl(chunks: list[SopChunk], output_path: Path = DEFAULT_OUTPUT_PATH) -> None:
    if not chunks:
        raise ValueError("Cannot write empty chunk list")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def ingest_corpus(
    corpus_dir: Path = DEFAULT_CORPUS_DIR,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> list[SopChunk]:
    chunks = load_corpus_chunks(corpus_dir)
    write_chunks_jsonl(chunks, output_path)
    return chunks


def main() -> None:
    chunks = ingest_corpus()
    print(f"Wrote {len(chunks)} chunks to {DEFAULT_OUTPUT_PATH}")


if __name__ == "__main__":
    main()