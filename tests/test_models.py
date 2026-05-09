import pytest
from pydantic import ValidationError

from rag_doc_models import DocumentChunk, SourceDocument

def test_source_document_accepts_required_fields():
    doc = SourceDocument(
        document_id="sop-001",
        source_path="data/sample/controlled-substances-sop.md",
        title="First Syntheic SOP"
    )

    assert doc.document_id=="sop-001"
    assert doc.version is None

def test_document_chunk_accepts_optional_metadata():
    chunk = DocumentChunk(
        chunk_id="sop-001-0001",
        document_id="sop-001",
        text="Any controlled substance discrepancy must be documented before end of shift.",
        source_path="data/sample/controlled-substances-sop.md",
        section="Discrepancy Review",
        version="0.1",
    )

    assert chunk.section == "Discrepancy Review"
    assert chunk.page is None


def test_document_chunk_rejects_empty_text():
    with pytest.raises(ValidationError):
        DocumentChunk(
            chunk_id="sop-001-0001",
            document_id="sop-001",
            text="",
            source_path="data/sample/controlled-substances-sop.md",
        )