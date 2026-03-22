"""Knowledge graph retrieval wrapper."""

from __future__ import annotations

from ..storage.graph_store import Neo4jGraphStore
from ..storage.vector_store import SearchResult


class GraphRetriever:
	"""Retrieve graph-neighbor evidence for a query entity."""

	def __init__(self, graph_store: Neo4jGraphStore) -> None:
		self.graph_store = graph_store

	async def retrieve(self, query: str, k: int) -> list[SearchResult]:
		chunks = await self.graph_store.search_related(query=query, depth=2)
		return [SearchResult(chunk=c, score=1.0 / (idx + 1), source="graph") for idx, c in enumerate(chunks[:k])]


__all__ = ["GraphRetriever"]
