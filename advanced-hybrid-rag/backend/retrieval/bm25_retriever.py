"""BM25 sparse retriever wrapper."""

from __future__ import annotations

from ..storage.bm25_store import BM25Store
from ..storage.vector_store import SearchResult


class BM25Retriever:
	"""Run keyword retrieval against the BM25 store."""

	def __init__(self, bm25_store: BM25Store) -> None:
		self.bm25_store = bm25_store

	async def retrieve(self, query: str, k: int) -> list[SearchResult]:
		results = self.bm25_store.search(query=query, k=k)
		return [SearchResult(chunk=r.chunk, score=r.score, source="bm25") for r in results]


__all__ = ["BM25Retriever"]
