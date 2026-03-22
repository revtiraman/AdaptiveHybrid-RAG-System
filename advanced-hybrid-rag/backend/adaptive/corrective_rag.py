"""Corrective RAG loop implementation."""

from __future__ import annotations

from collections import Counter
from typing import Awaitable, Callable

from ..ingestion.models import Chunk


class CorrectiveRAG:
	"""Run CRAG classification/refinement loop on retrieved chunks."""

	def __init__(
		self,
		regenerate_answer: Callable[[str, list[Chunk]], Awaitable[dict]] | None = None,
		refine_retrieval: Callable[[str, list[Chunk]], Awaitable[list[Chunk]]] | None = None,
	) -> None:
		self.regenerate_answer = regenerate_answer
		self.refine_retrieval = refine_retrieval

	async def run(self, query: str, initial_result: dict, retrieved_chunks: list[Chunk]) -> dict:
		labels = [self.classify_chunk(query, chunk) for chunk in retrieved_chunks]
		counts = Counter(labels)

		if counts.get("INCORRECT", 0) > max(1, len(retrieved_chunks) // 2):
			refined_chunks = await self.refine_knowledge(query, [c for c, l in zip(retrieved_chunks, labels) if l == "INCORRECT"])
			if self.regenerate_answer is not None:
				regenerated = await self.regenerate_answer(query, refined_chunks)
				regenerated.setdefault("warnings", []).append("Corrective RAG regeneration applied.")
				return regenerated
			initial_result.setdefault("warnings", []).append("Corrective RAG requested but regenerate handler is unavailable.")
			return initial_result

		initial_result.setdefault("warnings", []).append("Corrective RAG check passed without re-retrieval.")
		return initial_result

	def classify_chunk(self, query: str, chunk: Chunk) -> str:
		q_terms = set(query.lower().split())
		c_terms = set(chunk.text.lower().split())
		overlap = len(q_terms & c_terms) / (len(q_terms) or 1)
		if overlap >= 0.35:
			return "CORRECT"
		if overlap >= 0.15:
			return "AMBIGUOUS"
		return "INCORRECT"

	async def refine_knowledge(self, query: str, bad_chunks: list[Chunk]) -> list[Chunk]:
		if self.refine_retrieval is None:
			return []
		return await self.refine_retrieval(query, bad_chunks)


__all__ = ["CorrectiveRAG"]
