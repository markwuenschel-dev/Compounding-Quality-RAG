from pydantic import BaseModel, Field

class SourceDocument(BaseModel):
    document_id: str = Field(min_length=1) # rejects non empty strings
    source_path: str = Field(min_length=1)
    title: str = Field(min_length=1)
    version: str | None = None # string may be null or empty, and if missing, use None
    effective_date: str | None = None

class DocumentChunk(BaseModel):
    chunk_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    section: str | None = None
    page: int | None = None
    version: str | None = None