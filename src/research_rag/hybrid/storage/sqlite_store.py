from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from research_rag.hybrid.domain import ClaimRecord, PaperRecord, SectionChunk


class MetadataStore:
    def __init__(self, sqlite_path: Path) -> None:
        self.sqlite_path = sqlite_path

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS papers (
                    paper_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    page_count INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    paper_id TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    section TEXT NOT NULL,
                    ordinal INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    char_count INTEGER NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(paper_id) REFERENCES papers(paper_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_chunks_paper ON chunks(paper_id);
                CREATE INDEX IF NOT EXISTS idx_chunks_section ON chunks(section);
                CREATE INDEX IF NOT EXISTS idx_chunks_page ON chunks(page_number);

                CREATE TABLE IF NOT EXISTS claims (
                    claim_id TEXT PRIMARY KEY,
                    paper_id TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    claim TEXT NOT NULL,
                    claim_type TEXT NOT NULL,
                    section TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    entities_json TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(paper_id) REFERENCES papers(paper_id) ON DELETE CASCADE,
                    FOREIGN KEY(chunk_id) REFERENCES chunks(chunk_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_claims_paper ON claims(paper_id);
                CREATE INDEX IF NOT EXISTS idx_claims_type ON claims(claim_type);
                """
            )

    def upsert_paper(self, paper: PaperRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO papers (
                    paper_id, title, source_path, checksum, page_count, chunk_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(paper_id) DO UPDATE SET
                    title=excluded.title,
                    source_path=excluded.source_path,
                    checksum=excluded.checksum,
                    page_count=excluded.page_count,
                    chunk_count=excluded.chunk_count,
                    updated_at=excluded.updated_at
                """,
                (
                    paper.paper_id,
                    paper.title,
                    paper.source_path,
                    paper.checksum,
                    paper.page_count,
                    paper.chunk_count,
                    paper.created_at,
                    paper.updated_at,
                ),
            )

    def replace_chunks(self, paper_id: str, chunks: list[SectionChunk], created_at: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM chunks WHERE paper_id = ?", (paper_id,))
            conn.executemany(
                """
                INSERT INTO chunks (
                    chunk_id, paper_id, page_number, section, ordinal, text, char_count, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.chunk_id,
                        chunk.paper_id,
                        chunk.page_number,
                        chunk.section,
                        chunk.ordinal,
                        chunk.text,
                        chunk.char_count,
                        json.dumps(chunk.metadata),
                        created_at,
                    )
                    for chunk in chunks
                ],
            )

    def list_papers(self) -> list[PaperRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM papers ORDER BY updated_at DESC").fetchall()
        return [
            PaperRecord(
                paper_id=row["paper_id"],
                title=row["title"],
                source_path=row["source_path"],
                checksum=row["checksum"],
                page_count=row["page_count"],
                chunk_count=row["chunk_count"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def get_paper(self, paper_id: str) -> PaperRecord | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM papers WHERE paper_id = ?", (paper_id,)).fetchone()
        if row is None:
            return None
        return PaperRecord(
            paper_id=row["paper_id"],
            title=row["title"],
            source_path=row["source_path"],
            checksum=row["checksum"],
            page_count=row["page_count"],
            chunk_count=row["chunk_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def fetch_chunks(self, paper_ids: list[str] | None = None) -> list[SectionChunk]:
        sql = "SELECT * FROM chunks"
        params: tuple[object, ...] = ()
        if paper_ids:
            placeholders = ", ".join(["?"] * len(paper_ids))
            sql += f" WHERE paper_id IN ({placeholders})"
            params = tuple(paper_ids)
        sql += " ORDER BY paper_id, ordinal ASC"

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        chunks: list[SectionChunk] = []
        for row in rows:
            chunks.append(
                SectionChunk(
                    chunk_id=row["chunk_id"],
                    paper_id=row["paper_id"],
                    page_number=row["page_number"],
                    section=row["section"],
                    ordinal=row["ordinal"],
                    text=row["text"],
                    char_count=row["char_count"],
                    metadata=json.loads(row["metadata_json"]),
                )
            )
        return chunks

    def count_chunks(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM chunks").fetchone()
        return int(row["c"])

    def replace_claims(self, paper_id: str, claims: list[ClaimRecord], created_at: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM claims WHERE paper_id = ?", (paper_id,))
            if not claims:
                return
            conn.executemany(
                """
                INSERT INTO claims (
                    claim_id, paper_id, chunk_id, claim, claim_type, section,
                    page_number, entities_json, confidence, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        claim.claim_id,
                        claim.paper_id,
                        claim.chunk_id,
                        claim.claim,
                        claim.claim_type,
                        claim.section,
                        claim.page_number,
                        json.dumps(claim.entities),
                        claim.confidence,
                        json.dumps(claim.metadata),
                        created_at,
                    )
                    for claim in claims
                ],
            )

    def count_claims(self, paper_id: str | None = None) -> int:
        with self._connect() as conn:
            if paper_id:
                row = conn.execute("SELECT COUNT(*) AS c FROM claims WHERE paper_id = ?", (paper_id,)).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) AS c FROM claims").fetchone()
        return int(row["c"])

    def fetch_chunk_samples(self, paper_id: str, limit: int = 5) -> list[dict[str, object]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT c.chunk_id, c.paper_id, c.page_number, c.section, c.ordinal, c.text,
                       COUNT(cl.claim_id) AS claim_count
                FROM chunks c
                LEFT JOIN claims cl ON c.chunk_id = cl.chunk_id
                WHERE c.paper_id = ?
                GROUP BY c.chunk_id, c.paper_id, c.page_number, c.section, c.ordinal, c.text
                ORDER BY c.ordinal ASC
                LIMIT ?
                """,
                (paper_id, max(1, int(limit))),
            ).fetchall()

        out: list[dict[str, object]] = []
        for row in rows:
            text = str(row["text"] or "")
            lower = text.lower()
            out.append(
                {
                    "chunk_id": row["chunk_id"],
                    "paper_id": row["paper_id"],
                    "page_number": int(row["page_number"]),
                    "section": row["section"],
                    "ordinal": int(row["ordinal"]),
                    "text_preview": text[:320],
                    "char_count": len(text),
                    "claim_count": int(row["claim_count"]),
                    "looks_like_reference": bool(
                        re.search(r"\[\d+\]\s+[A-Z][a-z]+", text)
                        or re.search(r"(?m)^\s*\d+\.\s+[A-Z][a-z]+.+\(\d{4}\)", text)
                    ),
                    "looks_like_noise": any(
                        marker in lower
                        for marker in ["example query", "grounding:", "mode:", "sub-questions generated"]
                    ),
                }
            )
        return out

    def fetch_paper_structure(self, paper_id: str) -> dict[str, object]:
        chunks = self.fetch_chunks([paper_id])

        section_chunk_counts: dict[str, int] = {}
        section_table_counts: dict[str, int] = {}
        noisy_chunks = 0
        reference_chunks = 0

        for chunk in chunks:
            section = (chunk.section or "unknown").strip().lower() or "unknown"
            section_chunk_counts[section] = section_chunk_counts.get(section, 0) + 1
            if str(chunk.metadata.get("content_type", "")).lower() == "table":
                section_table_counts[section] = section_table_counts.get(section, 0) + 1

            lower = (chunk.text or "").lower()
            if any(marker in lower for marker in ["example query", "grounding:", "mode:", "sub-questions generated"]):
                noisy_chunks += 1
            if re.search(r"\[\d+\]\s+[A-Z][a-z]+", chunk.text or ""):
                reference_chunks += 1

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT section, COUNT(*) AS c
                FROM claims
                WHERE paper_id = ?
                GROUP BY section
                """,
                (paper_id,),
            ).fetchall()

        section_claim_counts = {str(row["section"] or "unknown").strip().lower(): int(row["c"]) for row in rows}

        sections: list[dict[str, object]] = []
        for section in sorted(set(section_chunk_counts) | set(section_claim_counts) | set(section_table_counts)):
            sections.append(
                {
                    "section": section,
                    "chunk_count": section_chunk_counts.get(section, 0),
                    "claim_count": section_claim_counts.get(section, 0),
                    "table_count": section_table_counts.get(section, 0),
                }
            )

        return {
            "paper_id": paper_id,
            "section_count": len(sections),
            "total_chunks": len(chunks),
            "total_claims": sum(section_claim_counts.values()),
            "total_tables": sum(section_table_counts.values()),
            "reference_chunk_count": reference_chunks,
            "noisy_chunk_count": noisy_chunks,
            "sections": sections,
        }

    def delete_paper(self, paper_id: str) -> bool:
        """Delete a paper and all its associated data. Returns True if the paper existed."""
        with self._connect() as conn:
            row = conn.execute("SELECT 1 FROM papers WHERE paper_id = ?", (paper_id,)).fetchone()
            if row is None:
                return False
            conn.execute("DELETE FROM claims WHERE paper_id = ?", (paper_id,))
            conn.execute("DELETE FROM chunks WHERE paper_id = ?", (paper_id,))
            conn.execute("DELETE FROM papers WHERE paper_id = ?", (paper_id,))
        return True
