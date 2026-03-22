"""Hypothetical Document Embeddings retriever."""

from __future__ import annotations

import asyncio
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
		direct_weight: float = 0.6,
		hyde_weight: float = 0.4,
	) -> None:
		self.vector_store = vector_store
		self.embedder = embedder
		self.llm_generate = llm_generate
		self.direct_weight = direct_weight
		self.hyde_weight = hyde_weight

	async def retrieve(self, query: str, k: int) -> list[SearchResult]:
		hypo_prompt = (
			"Write a short research paper excerpt that would answer the following question: "
			f"{query}"
		)
		hypothetical = await self._generate_hypothetical(hypo_prompt, query)

		hypo_emb = self.embedder.embed_query(hypothetical)
		query_emb = self.embedder.embed_query(query)

		hypo_results, direct_results = await self._parallel_search(hypo_emb, query_emb, k)
		merged = {
			r.chunk.metadata.chunk_id: SearchResult(chunk=r.chunk, score=r.score * self.direct_weight, source=r.source)
			for r in direct_results
		}
		for res in hypo_results:
			key = res.chunk.metadata.chunk_id
			hyde_score = res.score * self.hyde_weight
			if key in merged:
				merged[key].score = merged[key].score + hyde_score
			else:
				merged[key] = SearchResult(chunk=res.chunk, score=hyde_score, source="hyde")
		ranked = sorted(merged.values(), key=lambda x: x.score, reverse=True)
		return ranked[:k]

	async def _parallel_search(self, hypo_emb, query_emb, k: int):
		hypo = self.vector_store.search(hypo_emb, k=k, filter=None)
		direct = self.vector_store.search(query_emb, k=k, filter=None)
		return await asyncio.gather(hypo, direct)

	async def _generate_hypothetical(self, prompt: str, fallback: str) -> str:
		if self.llm_generate is None:
			return fallback
		try:
			out = await self.llm_generate(prompt)
			return out.strip() or fallback
		except Exception:
			return fallback


__all__ = ["HyDERetriever"]
