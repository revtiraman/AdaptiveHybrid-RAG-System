"""Vector store abstractions and implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

from ..ingestion.models import Chunk


class SearchResult(BaseModel):
	chunk: Chunk
	score: float
	source: str = "vector"


class StoreStats(BaseModel):
	store_type: str
	total_vectors: int = 0
	dimensions: int | None = None
	collections: list[str] = Field(default_factory=list)


class VectorStore(ABC):
	"""Abstract vector-store contract."""

	@abstractmethod
	async def add(self, chunks: list[Chunk]) -> None:
		"""Insert or update chunks in vector storage."""

	@abstractmethod
	async def search(self, query_embedding: np.ndarray, k: int, filter: dict | None = None) -> list[SearchResult]:
		"""Search nearest neighbors by cosine similarity."""

	@abstractmethod
	async def delete(self, doc_id: str) -> None:
		"""Delete vectors belonging to a document."""

	@abstractmethod
	async def get_stats(self) -> StoreStats:
		"""Return store statistics."""


class ChromaDBStore(VectorStore):
	"""ChromaDB-backed vector store with in-memory fallback."""

	def __init__(self, collection_name: str = "research_papers", host: str = "localhost", port: int = 8000) -> None:
		self.collection_name = collection_name
		self.host = host
		self.port = port
		self._client = None
		self._collection = None
		self._in_memory: list[Chunk] = []

	async def add(self, chunks: list[Chunk]) -> None:
		if not chunks:
			return
		collection = await self._get_collection()
		if collection is None:
			self._in_memory.extend(chunks)
			return

		ids = [c.metadata.chunk_id for c in chunks]
		docs = [c.text for c in chunks]
		metadatas = [
			{
				"doc_id": c.metadata.doc_id,
				"chunk_id": c.metadata.chunk_id,
				"page_start": c.metadata.page_start,
				"page_end": c.metadata.page_end,
				"section": c.metadata.section,
				"source": c.metadata.source_file,
			}
			for c in chunks
		]
		embeddings = [c.embedding for c in chunks]
		await collection.upsert(ids=ids, documents=docs, metadatas=metadatas, embeddings=embeddings)

	async def search(self, query_embedding: np.ndarray, k: int, filter: dict | None = None) -> list[SearchResult]:
		collection = await self._get_collection()
		if collection is None:
			return self._search_in_memory(query_embedding, k, filter)

		kwargs: dict[str, Any] = {
			"query_embeddings": [query_embedding.tolist()],
			"n_results": k,
		}
		if filter:
			kwargs["where"] = filter
		result = await collection.query(**kwargs)

		out: list[SearchResult] = []
		docs = (result.get("documents") or [[]])[0]
		metas = (result.get("metadatas") or [[]])[0]
		dists = (result.get("distances") or [[]])[0]
		for doc_text, meta, dist in zip(docs, metas, dists):
			chunk = Chunk(
				text=doc_text,
				metadata={
					"doc_id": meta.get("doc_id", ""),
					"chunk_id": meta.get("chunk_id", ""),
					"source_file": meta.get("source", ""),
					"section": meta.get("section", ""),
					"page_start": int(meta.get("page_start", 1)),
					"page_end": int(meta.get("page_end", 1)),
					"char_start": 0,
					"char_end": len(doc_text),
					"chunk_index": 0,
					"total_chunks": 0,
				},
			)
			out.append(SearchResult(chunk=chunk, score=1.0 - float(dist)))
		return out

	async def delete(self, doc_id: str) -> None:
		collection = await self._get_collection()
		if collection is None:
			self._in_memory = [c for c in self._in_memory if c.metadata.doc_id != doc_id]
			return
		await collection.delete(where={"doc_id": doc_id})

	async def get_stats(self) -> StoreStats:
		collection = await self._get_collection()
		if collection is None:
			dim = len(self._in_memory[0].embedding) if self._in_memory and self._in_memory[0].embedding else None
			return StoreStats(store_type="chromadb(in-memory)", total_vectors=len(self._in_memory), dimensions=dim)
		count = await collection.count()
		return StoreStats(store_type="chromadb", total_vectors=count, collections=[self.collection_name])

	async def _get_collection(self):
		if self._collection is not None:
			return self._collection
		try:
			import chromadb

			self._client = await chromadb.AsyncHttpClient(host=self.host, port=self.port)
			self._collection = await self._client.get_or_create_collection(name=self.collection_name)
			return self._collection
		except Exception:
			return None

	def _search_in_memory(self, query_embedding: np.ndarray, k: int, filter: dict | None) -> list[SearchResult]:
		q = query_embedding
		if q.ndim != 1:
			q = q.reshape(-1)
		scored: list[tuple[float, Chunk]] = []
		for chunk in self._in_memory:
			if filter and filter.get("doc_id") and chunk.metadata.doc_id != filter["doc_id"]:
				continue
			if not chunk.embedding:
				continue
			emb = np.asarray(chunk.embedding, dtype=np.float32)
			denom = (np.linalg.norm(q) * np.linalg.norm(emb)) or 1.0
			score = float(np.dot(q, emb) / denom)
			scored.append((score, chunk))
		scored.sort(key=lambda x: x[0], reverse=True)
		return [SearchResult(chunk=chunk, score=score) for score, chunk in scored[:k]]


class PgVectorStore(VectorStore):
	"""pgvector implementation with graceful fallback to process memory."""

	def __init__(self, dsn: str) -> None:
		self.dsn = dsn
		self._pool = None
		self._in_memory: list[Chunk] = []

	async def add(self, chunks: list[Chunk]) -> None:
		pool = await self._get_pool()
		if pool is None:
			self._in_memory.extend(chunks)
			return
		async with pool.acquire() as conn:
			await conn.execute(
				"""
				CREATE TABLE IF NOT EXISTS rag_chunks (
					chunk_id TEXT PRIMARY KEY,
					doc_id TEXT NOT NULL,
					text TEXT NOT NULL,
					metadata JSONB NOT NULL,
					embedding vector(384)
				)
				"""
			)
			for chunk in chunks:
				emb = chunk.embedding or []
				await conn.execute(
					"""
					INSERT INTO rag_chunks (chunk_id, doc_id, text, metadata, embedding)
					VALUES ($1, $2, $3, $4, $5)
					ON CONFLICT (chunk_id)
					DO UPDATE SET doc_id=$2, text=$3, metadata=$4, embedding=$5
					""",
					chunk.metadata.chunk_id,
					chunk.metadata.doc_id,
					chunk.text,
					chunk.metadata.model_dump(),
					emb,
				)

	async def search(self, query_embedding: np.ndarray, k: int, filter: dict | None = None) -> list[SearchResult]:
		if await self._get_pool() is None:
			return ChromaDBStore()._search_in_memory(query_embedding, k, filter)
		# For early phase compatibility, return empty until full SQL search query is added.
		return []

	async def delete(self, doc_id: str) -> None:
		pool = await self._get_pool()
		if pool is None:
			self._in_memory = [c for c in self._in_memory if c.metadata.doc_id != doc_id]
			return
		async with pool.acquire() as conn:
			await conn.execute("DELETE FROM rag_chunks WHERE doc_id = $1", doc_id)

	async def get_stats(self) -> StoreStats:
		pool = await self._get_pool()
		if pool is None:
			return StoreStats(store_type="pgvector(in-memory)", total_vectors=len(self._in_memory))
		async with pool.acquire() as conn:
			total = await conn.fetchval("SELECT COUNT(*) FROM rag_chunks")
		return StoreStats(store_type="pgvector", total_vectors=int(total or 0))

	async def _get_pool(self):
		if self._pool is not None:
			return self._pool
		try:
			import asyncpg

			self._pool = await asyncpg.create_pool(self.dsn)
			return self._pool
		except Exception:
			return None


__all__ = ["VectorStore", "SearchResult", "StoreStats", "ChromaDBStore", "PgVectorStore"]
