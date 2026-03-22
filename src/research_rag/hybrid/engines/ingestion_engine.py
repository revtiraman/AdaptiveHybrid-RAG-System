from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from research_rag.hybrid.domain import PaperRecord
from research_rag.hybrid.utils import sha256_bytes, stable_id, utc_now_iso


@dataclass(slots=True)
class IngestionReport:
    paper_id: str
    title: str
    page_count: int
    chunk_count: int
    source_path: str

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "page_count": self.page_count,
            "chunk_count": self.chunk_count,
            "source_path": self.source_path,
        }


class IngestionEngine:
    def __init__(self, settings, parser, chunker, embedder, vector_store, metadata_store) -> None:
        self.settings = settings
        self.parser = parser
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.metadata_store = metadata_store

    def ingest_pdf(self, pdf_path: str | Path, title: str | None = None, paper_id: str | None = None) -> IngestionReport:
        source_path = Path(pdf_path).expanduser().resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"PDF file does not exist: {source_path}")
        if source_path.suffix.lower() != ".pdf":
            raise ValueError("Only PDF files are supported")

        payload = source_path.read_bytes()
        checksum = sha256_bytes(payload)

        resolved_title = (title or source_path.stem).strip() or source_path.stem
        resolved_paper_id = paper_id or stable_id("paper", f"{resolved_title}-{checksum[:16]}")
        managed_path = self.settings.documents_dir / f"{resolved_paper_id}.pdf"
        managed_path.write_bytes(payload)

        pages = self.parser.parse_pages(managed_path)
        chunks = self.chunker.chunk_document(resolved_paper_id, pages)
        if not chunks:
            raise ValueError("Could not extract retrievable chunks from this PDF")

        embeddings = self.embedder.embed([c.text for c in chunks])
        now = utc_now_iso()

        paper = PaperRecord(
            paper_id=resolved_paper_id,
            title=resolved_title,
            source_path=str(managed_path),
            checksum=checksum,
            page_count=len(pages),
            chunk_count=len(chunks),
            created_at=now,
            updated_at=now,
        )
        self.metadata_store.upsert_paper(paper)
        self.metadata_store.replace_chunks(resolved_paper_id, chunks, created_at=now)
        self.vector_store.upsert(chunks, embeddings)

        return IngestionReport(
            paper_id=resolved_paper_id,
            title=resolved_title,
            page_count=len(pages),
            chunk_count=len(chunks),
            source_path=str(managed_path),
        )
