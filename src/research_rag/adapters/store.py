from __future__ import annotations

import json
import math
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator

from research_rag.domain import Chunk, DocumentRecord, SearchResult


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left or not right:
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    dot = sum(left_value * right_value for left_value, right_value in zip(left, right, strict=False))
    return dot / (left_norm * right_norm)


class SqliteVectorStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    source_path TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    page_count INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    ordinal INTEGER NOT NULL,
                    page_number INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    token_count INTEGER NOT NULL,
                    metadata_json TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(document_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
                CREATE INDEX IF NOT EXISTS idx_chunks_document_ordinal ON chunks(document_id, ordinal);
                """
            )

    def upsert_document(self, document: DocumentRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    document_id,
                    source_path,
                    source_name,
                    checksum,
                    page_count,
                    chunk_count,
                    metadata_json,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    source_path = excluded.source_path,
                    source_name = excluded.source_name,
                    checksum = excluded.checksum,
                    page_count = excluded.page_count,
                    chunk_count = excluded.chunk_count,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    document.document_id,
                    document.source_path,
                    document.source_name,
                    document.checksum,
                    document.page_count,
                    document.chunk_count,
                    json.dumps(document.metadata),
                    document.created_at or document.updated_at,
                    document.updated_at or document.created_at,
                ),
            )

    def replace_chunks(self, document_id: str, items: Iterable[tuple[Chunk, list[float]]], created_at: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            connection.executemany(
                """
                INSERT INTO chunks (
                    chunk_id,
                    document_id,
                    ordinal,
                    page_number,
                    text,
                    token_count,
                    metadata_json,
                    embedding_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.chunk_id,
                        chunk.document_id,
                        chunk.ordinal,
                        chunk.page_number,
                        chunk.text,
                        chunk.token_count,
                        json.dumps(chunk.metadata),
                        json.dumps(embedding),
                        created_at,
                    )
                    for chunk, embedding in items
                ],
            )

    def list_documents(self) -> list[DocumentRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM documents ORDER BY updated_at DESC, document_id ASC"
            ).fetchall()
        return [self._document_from_row(row) for row in rows]

    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        document_id: str | None = None,
        document_ids: list[str] | None = None,
    ) -> list[SearchResult]:
        if top_k <= 0:
            return []

        sql = "SELECT * FROM chunks"
        params: tuple[object, ...] = ()
        if document_id:
            sql += " WHERE document_id = ?"
            params = (document_id,)
        elif document_ids is not None:
            if not document_ids:
                return []
            placeholders = ", ".join(["?"] * len(document_ids))
            sql += f" WHERE document_id IN ({placeholders})"
            params = tuple(document_ids)

        with self._connect() as connection:
            rows = connection.execute(sql, params).fetchall()

        scored: list[SearchResult] = []
        for row in rows:
            embedding = json.loads(row["embedding_json"])
            score = _cosine_similarity(query_embedding, embedding)
            chunk = self._chunk_from_row(row)
            scored.append(SearchResult(chunk=chunk, score=score))

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    @staticmethod
    def _document_from_row(row: sqlite3.Row) -> DocumentRecord:
        return DocumentRecord(
            document_id=row["document_id"],
            source_path=row["source_path"],
            source_name=row["source_name"],
            checksum=row["checksum"],
            page_count=row["page_count"],
            chunk_count=row["chunk_count"],
            metadata=json.loads(row["metadata_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _chunk_from_row(row: sqlite3.Row) -> Chunk:
        return Chunk(
            chunk_id=row["chunk_id"],
            document_id=row["document_id"],
            ordinal=row["ordinal"],
            page_number=row["page_number"],
            text=row["text"],
            token_count=row["token_count"],
            metadata=json.loads(row["metadata_json"]),
        )
