from __future__ import annotations

from pathlib import Path

from app.retrieval import KeywordRetriever, load_chunks
from app.retrieval_query_strategy import RuleIntentQueryStrategy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "index" / "chunks.jsonl"


def retrieved_source_ids(query: str) -> list[str]:
    retriever = KeywordRetriever(load_chunks(CHUNKS_PATH))
    built_query = RuleIntentQueryStrategy().build(query)
    results = retriever.search(
        built_query.search_text,
        top_k=5,
        source_type="sop",
    )

    source_ids: list[str] = []
    for result in results:
        source_id = result["chunk"]["source_id"]
        if source_id not in source_ids:
            source_ids.append(source_id)
    return source_ids


def test_neurologic_event_does_not_route_to_supplier_guidance() -> None:
    source_ids = retrieved_source_ids(
        "After first dose given around 20 minutes prior to eating, within half an hour the pet had difficulty walking and general weakness. Will not report to manufacturer."
    )

    assert source_ids[0] == "SOP-005"
    assert "SOP-002" not in source_ids


def test_ingredient_composition_request_retrieves_boundary_guidance() -> None:
    source_ids = retrieved_source_ids(
        "The customer wants to know what inactive ingredients are in the oral oil suspension, including vegan flavoring and sugar-free specifics."
    )

    assert "SOP-002" in source_ids or "SOP-005" in source_ids
    assert "SOP-007" not in source_ids
