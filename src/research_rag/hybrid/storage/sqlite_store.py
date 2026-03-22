from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from research_rag.hybrid.domain import PaperRecord, SectionChunk


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
