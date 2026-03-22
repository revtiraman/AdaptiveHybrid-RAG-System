"""Dense vector retriever wrapper."""

from __future__ import annotations

import numpy as np

from ..storage.vector_store import SearchResult, VectorStore


class VectorRetriever:
	"""Run dense nearest-neighbor retrieval against a vector store."""

	def __init__(self, vector_store: VectorStore) -> None:
		self.vector_store = vector_store

	async def retrieve(self, query_embedding: np.ndarray, k: int, filters: dict | None = None) -> list[SearchResult]:
		return await self.vector_store.search(query_embedding=query_embedding, k=k, filter=filters)


__all__ = ["VectorRetriever"]
