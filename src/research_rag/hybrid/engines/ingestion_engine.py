from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from research_rag.hybrid.engines.claim_extractor import ClaimExtractor
from research_rag.hybrid.engines.table_processor import TableProcessor
from research_rag.hybrid.domain import PaperRecord
from research_rag.hybrid.utils import sha256_bytes, stable_id, utc_now_iso


@dataclass(slots=True)
class IngestionReport:
    paper_id: str
    title: str
    page_count: int
    chunk_count: int
    source_path: str
    elements_by_type: dict[str, int]
    sections_detected: list[str]
    layout_columns: int
    extraction_quality_score: float
    claims_extracted: int

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "page_count": self.page_count,
            "chunk_count": self.chunk_count,
            "source_path": self.source_path,
            "elements_by_type": self.elements_by_type,
            "sections_detected": self.sections_detected,
            "layout_columns": self.layout_columns,
            "extraction_quality_score": self.extraction_quality_score,
            "claims_extracted": self.claims_extracted,
        }


class IngestionEngine:
    def __init__(self, settings, parser, chunker, embedder, vector_store, metadata_store) -> None:
        self.settings = settings
        self.parser = parser
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.metadata_store = metadata_store
        self.claim_extractor = ClaimExtractor()
        self.table_processor = TableProcessor()

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
        table_chunks = self.table_processor.extract_table_chunks(
            managed_path,
            resolved_paper_id,
            start_ordinal=len(chunks),
        )
        if table_chunks:
            chunks.extend(table_chunks)
        if not chunks:
            raise ValueError("Could not extract retrievable chunks from this PDF")

        elements_by_type: dict[str, int] = {}
        sections_detected: set[str] = set()
        columns_detected = 1
        quality_values: list[float] = []
        for page in pages:
            columns_detected = max(columns_detected, int(page.get("layout_columns", 1) or 1))
            quality_values.append(float(page.get("extraction_quality_score", 0.0) or 0.0))
            section_value = str(page.get("section", "") or "").strip()
            if section_value:
                sections_detected.add(section_value)
            for element_type, count in dict(page.get("elements_by_type", {}) or {}).items():
                key = str(element_type)
                elements_by_type[key] = elements_by_type.get(key, 0) + int(count)

        if not elements_by_type:
            elements_by_type = {"paragraph": len(pages)}
        if table_chunks:
            elements_by_type["table"] = len(table_chunks)

        quality_score = sum(quality_values) / max(1, len(quality_values))

        embeddings = self.embedder.embed([c.text for c in chunks])
        claims = self.claim_extractor.extract_from_chunks(chunks)
        claim_embeddings = self.embedder.embed([c.claim for c in claims]) if claims else []
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
        self.metadata_store.replace_claims(resolved_paper_id, claims, created_at=now)
        self.vector_store.upsert(chunks, embeddings)
        if claims:
            self.vector_store.upsert_claims(claims, claim_embeddings)

        return IngestionReport(
            paper_id=resolved_paper_id,
            title=resolved_title,
            page_count=len(pages),
            chunk_count=len(chunks),
            source_path=str(managed_path),
            elements_by_type=elements_by_type,
            sections_detected=sorted(sections_detected),
            layout_columns=columns_detected,
            extraction_quality_score=round(quality_score, 4),
            claims_extracted=len(claims),
        )
