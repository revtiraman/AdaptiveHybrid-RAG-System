"""Pydantic models used across the ingestion pipeline."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Reference(BaseModel):
    raw: str
    title: str | None = None
    year: int | None = None
    authors: list[str] = Field(default_factory=list)


class Table(BaseModel):
    page: int
    rows: list[list[str]] = Field(default_factory=list)


class Figure(BaseModel):
    page: int
    caption: str


class Section(BaseModel):
    name: str
    text: str
    page_start: int
    page_end: int


class DocumentMetadata(BaseModel):
    doc_id: str
    source: str
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    doi: str | None = None
    year: int | None = None
    venue: str | None = None
    language: str | None = None
    categories: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class ProcessedDocument(BaseModel):
    raw_text: str
    sections: list[Section] = Field(default_factory=list)
    metadata: DocumentMetadata
    tables: list[Table] = Field(default_factory=list)
    figures: list[Figure] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    math_equations: list[str] = Field(default_factory=list)


class ChunkMetadata(BaseModel):
    doc_id: str
    chunk_id: str
    source_file: str
    section: str
    page_start: int
    page_end: int
    char_start: int
    char_end: int
    chunk_index: int
    total_chunks: int
    is_table: bool = False
    is_caption: bool = False


class Chunk(BaseModel):
    text: str
    metadata: ChunkMetadata
    embedding: list[float] | None = None


class IngestionResult(BaseModel):
    doc_id: str
    source_type: str
    chunks_created: int
    entities_extracted: int
    ingestion_time_ms: float
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


__all__ = [
    "Reference",
    "Table",
    "Figure",
    "Section",
    "DocumentMetadata",
    "ProcessedDocument",
    "ChunkMetadata",
    "Chunk",
    "IngestionResult",
]
