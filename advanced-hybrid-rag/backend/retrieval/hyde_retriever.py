"""Hypothetical Document Embeddings retriever."""

from __future__ import annotations

from typing import Awaitable, Callable

from ..ingestion.embedder import BaseEmbedder
from ..storage.vector_store import SearchResult, VectorStore


class HyDERetriever:
	"""Use an LLM-generated hypothetical answer to improve retrieval recall."""

	def __init__(
		self,
		vector_store: VectorStore,
		embedder: BaseEmbedder,
		llm_generate: Callable[[str], Awaitable[str]] | None = None,
	) -> None:
		self.vector_store = vector_store
		self.embedder = embedder
		self.llm_generate = llm_generate

	async def retrieve(self, query: str, k: int) -> list[SearchResult]:
		hypo_prompt = (
			"Write a short research paper excerpt that would answer the following question: "
			f"{query}"
		)
		hypothetical = await self._generate_hypothetical(hypo_prompt, query)

		hypo_emb = self.embedder.embed_query(hypothetical)
		query_emb = self.embedder.embed_query(query)

		hypo_results, direct_results = await self._parallel_search(hypo_emb, query_emb, k)
		merged = {r.chunk.metadata.chunk_id: r for r in direct_results}
		for res in hypo_results:
			key = res.chunk.metadata.chunk_id
			if key in merged:
				merged[key].score = max(merged[key].score, res.score)
			else:
				merged[key] = res
		ranked = sorted(merged.values(), key=lambda x: x.score, reverse=True)
		return ranked[:k]

	async def _parallel_search(self, hypo_emb, query_emb, k: int):
		hypo = self.vector_store.search(hypo_emb, k=k, filter=None)
		direct = self.vector_store.search(query_emb, k=k, filter=None)
		return await hypo, await direct

	async def _generate_hypothetical(self, prompt: str, fallback: str) -> str:
		if self.llm_generate is None:
			return fallback
		try:
			out = await self.llm_generate(prompt)
			return out.strip() or fallback
		except Exception:
			return fallback


__all__ = ["HyDERetriever"]
