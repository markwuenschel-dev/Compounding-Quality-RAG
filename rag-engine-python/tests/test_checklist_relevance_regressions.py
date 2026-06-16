from app.checklist import (
    build_missing_information,
    build_retrieval_query,
    rerank_for_concern_type,
)
from app.retrieval import ChunkRecord, retrieve_from_chunks, tokenize
from app.schemas import ConcernType


def test_low_information_words_are_not_search_terms() -> None:
    terms = tokenize(
        "About ten minutes later he vomited once but seems okay now."
    )

    assert "about" not in terms
    assert "but" not in terms
    assert "vomited" in terms


def test_vomiting_query_expansion_adds_adverse_event_context() -> None:
    query = build_retrieval_query(
        "Dog vomited after an oral liquid.",
        ConcernType.FLAVOR_RELATED_VOMITING,
    )

    assert "suspected adverse event" in query
    assert "customer clinical context" in query


def test_vomiting_rerank_prefers_adverse_event_guidance() -> None:
    results = retrieve_from_chunks(
        query=(
            "Dog vomited after an oral liquid suspected adverse event "
            "customer clinical context hospitalization veterinarian"
        ),
        chunks=sample_chunks(),
        top_k=5,
        source_type="sop",
    )

    reranked = rerank_for_concern_type(
        results,
        ConcernType.FLAVOR_RELATED_VOMITING,
    )

    assert reranked[0]["chunk"]["chunk_id"] == "SOP-ADE::vomiting"


def test_missing_information_uses_explicit_customer_facts() -> None:
    missing = build_missing_information(
        "My dog received a chicken-flavored compounded oral liquid. "
        "About 10 minutes later he vomited once but seems okay now."
    )

    assert "Species" not in missing
    assert "Dosage form" not in missing
    assert "Timing of vomiting relative to administration" not in missing
    assert "Whether symptoms resolved" not in missing
    assert "Dose administered" in missing
    assert "Whether veterinarian was contacted" in missing
    assert "Whether the pet was hospitalized" in missing


def sample_chunks() -> list[ChunkRecord]:
    common = {
        "source_file": "test.md",
        "source_type": "sop",
        "process_area": "compounding_quality",
        "version": "1.0",
        "effective_date": "2026-01-01",
        "synthetic": True,
    }

    return [
        {
            **common,
            "chunk_id": "SOP-SHORTAGE::oral-liquid",
            "source_id": "SOP-SHORTAGE",
            "source_title": "Oral Liquid Shortage",
            "section_heading": "Oral Liquid Shortage",
            "text": "Routine oral liquid shortage and fill appearance guidance.",
        },
        {
            **common,
            "chunk_id": "SOP-ADE::vomiting",
            "source_id": "SOP-ADE",
            "source_title": "Adverse Event Review",
            "section_heading": "Vomiting and Clinical Context",
            "text": (
                "For a suspected adverse event involving vomiting, review "
                "customer clinical context, hospitalization, and veterinarian contact."
            ),
        },
    ]
