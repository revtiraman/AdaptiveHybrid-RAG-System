from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from research_rag.domain import Chunk, DocumentRecord
from research_rag.hybrid.config import HybridRAGSettings
from research_rag.hybrid.domain import PaperRecord, SectionChunk
from research_rag.hybrid.orchestrator import HybridRAGSystem
from research_rag.hybrid.storage.sqlite_store import MetadataStore
from research_rag.logging import configure_logging


class LegacyStoreAdapter:
    """Compatibility adapter for tests that still expect the old store API."""

    def __init__(self, metadata_store: MetadataStore) -> None:
        self._metadata_store = metadata_store

    def upsert_document(self, document: DocumentRecord) -> None:
        created_at = document.created_at or document.updated_at or self._now_iso()
        updated_at = document.updated_at or created_at
        self._metadata_store.upsert_paper(
            PaperRecord(
                paper_id=document.document_id,
                title=document.source_name or document.document_id,
                source_path=document.source_path,
                checksum=document.checksum,
                page_count=document.page_count,
                chunk_count=document.chunk_count,
                created_at=created_at,
                updated_at=updated_at,
            )
        )

    def replace_chunks(self, document_id: str, items: Iterable[tuple[Chunk, list[float]]], created_at: str) -> None:
        chunks = [
            SectionChunk(
                chunk_id=chunk.chunk_id,
                paper_id=chunk.document_id,
                page_number=chunk.page_number,
                section=str(chunk.metadata.get("section", "unknown")),
                ordinal=chunk.ordinal,
                text=chunk.text,
                char_count=len(chunk.text),
                metadata=dict(chunk.metadata),
            )
            for chunk, _ in items
        ]
        self._metadata_store.replace_chunks(document_id, chunks, created_at=created_at)

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class ServiceContainer:
    settings: HybridRAGSettings
    system: HybridRAGSystem
    store: LegacyStoreAdapter


def build_container(settings: HybridRAGSettings | None = None) -> ServiceContainer:
    resolved_settings = settings or HybridRAGSettings.from_env()
    configure_logging("INFO")

    system = HybridRAGSystem(resolved_settings)

    return ServiceContainer(
        settings=resolved_settings,
        system=system,
        store=LegacyStoreAdapter(system.metadata_store),
    )
