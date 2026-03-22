from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from research_rag.chunking import chunk_pages
from research_rag.domain import DocumentRecord
from research_rag.settings import Settings


@dataclass(slots=True)
class IngestionSummary:
    document_id: str
    source_name: str
    source_path: str
    checksum: str
    page_count: int
    chunk_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "document_id": self.document_id,
            "source_name": self.source_name,
            "source_path": self.source_path,
            "checksum": self.checksum,
            "page_count": self.page_count,
            "chunk_count": self.chunk_count,
        }


class DocumentIngestionService:
    def __init__(self, settings, pdf_loader, embedding_provider, store) -> None:
        self.settings: Settings = settings
        self.pdf_loader = pdf_loader
        self.embedding_provider = embedding_provider
        self.store = store

    def ingest_pdf(
        self,
        pdf_path: str | Path,
        document_id: str | None = None,
        metadata: dict[str, object] | None = None,
        id_namespace: str | None = None,
    ) -> IngestionSummary:
        source_path = Path(pdf_path).expanduser().resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"PDF file does not exist: {source_path}")
        if source_path.suffix.lower() != ".pdf":
            raise ValueError("Only PDF files are supported for ingestion")

        checksum = self._sha256(source_path)
        resolved_document_id = document_id or f"{source_path.stem.lower().replace(' ', '-')}-{checksum[:12]}"
        if id_namespace:
            resolved_document_id = f"{id_namespace}::{resolved_document_id}"
        managed_path = self.settings.documents_dir / f"{resolved_document_id}.pdf"
        if source_path != managed_path:
            shutil.copy2(source_path, managed_path)

        pages = self.pdf_loader.load_pages(managed_path)
        if not pages:
            raise ValueError("The PDF did not produce any extractable pages")

        chunks = chunk_pages(
            document_id=resolved_document_id,
            pages=pages,
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        if not chunks:
            raise ValueError("The PDF did not produce any retrievable chunks after processing")

        embeddings = self.embedding_provider.embed_texts([chunk.text for chunk in chunks])
        timestamp = datetime.now(UTC).isoformat()
        document = DocumentRecord(
            document_id=resolved_document_id,
            source_path=str(managed_path),
            source_name=source_path.name,
            checksum=checksum,
            page_count=len(pages),
            chunk_count=len(chunks),
            metadata={"original_path": str(source_path), **(metadata or {})},
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.store.upsert_document(document)
        self.store.replace_chunks(
            document_id=resolved_document_id,
            items=list(zip(chunks, embeddings, strict=True)),
            created_at=timestamp,
        )
        return IngestionSummary(
            document_id=resolved_document_id,
            source_name=source_path.name,
            source_path=str(managed_path),
            checksum=checksum,
            page_count=len(pages),
            chunk_count=len(chunks),
        )

    @staticmethod
    def _sha256(file_path: Path) -> str:
        digest = hashlib.sha256()
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
