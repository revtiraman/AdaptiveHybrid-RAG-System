"""Relational metadata store using SQLite."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ..ingestion.models import Chunk, DocumentMetadata


class RelationalStore:
	"""Simple SQLite store for documents and chunk metadata."""

	def __init__(self, db_path: str | Path = "data/metadata.sqlite3") -> None:
		self.db_path = Path(db_path)
		self.db_path.parent.mkdir(parents=True, exist_ok=True)
		self._init_db()

	def upsert_document(self, metadata: DocumentMetadata, chunks: list[Chunk]) -> None:
		conn = sqlite3.connect(self.db_path)
		try:
			conn.execute(
				"""
				INSERT INTO documents (doc_id, source, title, authors, doi, year, venue, language, extra)
				VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
				ON CONFLICT(doc_id) DO UPDATE SET
					source=excluded.source,
					title=excluded.title,
					authors=excluded.authors,
					doi=excluded.doi,
					year=excluded.year,
					venue=excluded.venue,
					language=excluded.language,
					extra=excluded.extra
				""",
				(
					metadata.doc_id,
					metadata.source,
					metadata.title,
					json.dumps(metadata.authors),
					metadata.doi,
					metadata.year,
					metadata.venue,
					metadata.language,
					json.dumps(metadata.extra),
				),
			)

			conn.execute("DELETE FROM chunks WHERE doc_id = ?", (metadata.doc_id,))
			conn.executemany(
				"""
				INSERT INTO chunks (
					chunk_id, doc_id, section, page_start, page_end,
					char_start, char_end, chunk_index, total_chunks, is_table, is_caption, text
				) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
				""",
				[
					(
						c.metadata.chunk_id,
						c.metadata.doc_id,
						c.metadata.section,
						c.metadata.page_start,
						c.metadata.page_end,
						c.metadata.char_start,
						c.metadata.char_end,
						c.metadata.chunk_index,
						c.metadata.total_chunks,
						int(c.metadata.is_table),
						int(c.metadata.is_caption),
						c.text,
					)
					for c in chunks
				],
			)
			conn.commit()
		finally:
			conn.close()

	def delete_document(self, doc_id: str) -> None:
		conn = sqlite3.connect(self.db_path)
		try:
			conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
			conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
			conn.commit()
		finally:
			conn.close()

	def list_documents(self) -> list[dict]:
		conn = sqlite3.connect(self.db_path)
		conn.row_factory = sqlite3.Row
		try:
			rows = conn.execute("SELECT * FROM documents ORDER BY rowid DESC").fetchall()
			return [dict(r) for r in rows]
		finally:
			conn.close()

	def _init_db(self) -> None:
		conn = sqlite3.connect(self.db_path)
		try:
			conn.execute(
				"""
				CREATE TABLE IF NOT EXISTS documents (
					doc_id TEXT PRIMARY KEY,
					source TEXT NOT NULL,
					title TEXT,
					authors TEXT,
					doi TEXT,
					year INTEGER,
					venue TEXT,
					language TEXT,
					extra TEXT
				)
				"""
			)
			conn.execute(
				"""
				CREATE TABLE IF NOT EXISTS chunks (
					chunk_id TEXT PRIMARY KEY,
					doc_id TEXT NOT NULL,
					section TEXT,
					page_start INTEGER,
					page_end INTEGER,
					char_start INTEGER,
					char_end INTEGER,
					chunk_index INTEGER,
					total_chunks INTEGER,
					is_table INTEGER,
					is_caption INTEGER,
					text TEXT
				)
				"""
			)
			conn.commit()
		finally:
			conn.close()


__all__ = ["RelationalStore"]
