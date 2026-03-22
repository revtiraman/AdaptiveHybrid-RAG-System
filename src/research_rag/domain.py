from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

JsonDict = dict[str, Any]


@dataclass(slots=True)
class SourcePage:
    page_number: int
    text: str
    metadata: JsonDict = field(default_factory=dict)


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    document_id: str
    ordinal: int
    page_number: int
    text: str
    token_count: int
    metadata: JsonDict = field(default_factory=dict)


@dataclass(slots=True)
class DocumentRecord:
    document_id: str
    source_path: str
    source_name: str
    checksum: str
    page_count: int
    chunk_count: int
    metadata: JsonDict = field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True)
class SearchResult:
    chunk: Chunk
    score: float


@dataclass(slots=True)
class AnswerPayload:
    answer: str
    citations: list[JsonDict]
    provider: str
