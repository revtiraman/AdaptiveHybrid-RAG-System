"""Corrective RAG loop implementation."""

from __future__ import annotations

from collections import Counter
from typing import Awaitable, Callable

from ..ingestion.models import Chunk
from .adaptive_controller import RetrievalParameters


class CorrectiveRAG:
	"""Run CRAG classification/refinement loop on retrieved chunks."""

	_STOPWORDS = {
		"a",
		"an",
		"the",
		"of",
		"to",
		"in",
		"on",
		"for",
		"with",
		"and",
		"or",
		"is",
		"are",
		"was",
		"were",
		"be",
		"that",
		"this",
	}

	def __init__(
		self,
		regenerate_answer: Callable[[str, list[Chunk]], Awaitable[dict]] | None = None,
		refine_retrieval: Callable[[str, list[Chunk]], Awaitable[list[Chunk]]] | None = None,
		optimize_retrieval: Callable[[str, list[Chunk]], Awaitable[RetrievalParameters | None]] | None = None,
		rerun_pipeline: Callable[[str, RetrievalParameters], Awaitable[dict]] | None = None,
	) -> None:
		self.regenerate_answer = regenerate_answer
		self.refine_retrieval = refine_retrieval
		self.optimize_retrieval = optimize_retrieval
		self.rerun_pipeline = rerun_pipeline

	async def run(self, query: str, initial_result: dict, retrieved_chunks: list[Chunk]) -> dict:
		labels = [self.classify_chunk(query, chunk) for chunk in retrieved_chunks]
		counts = Counter(labels)
		initial_result["corrective_labels"] = dict(counts)

		bad_labels = {"INCORRECT", "IRRELEVANT", "CONTRADICTORY"}
		bad_count = sum(count for label, count in counts.items() if label in bad_labels)

		if bad_count > max(1, len(retrieved_chunks) // 2):
			if self.optimize_retrieval is not None and self.rerun_pipeline is not None:
				params = await self.optimize_retrieval(query, retrieved_chunks)
				if params is not None:
					rerun = await self.rerun_pipeline(query, params)
					rerun["corrective_labels"] = dict(counts)
					rerun.setdefault("warnings", []).append("Corrective RAG full retrieval+generation rerun applied.")
					return rerun

			refined_chunks = await self.refine_knowledge(query, [c for c, l in zip(retrieved_chunks, labels) if l in bad_labels])
			if self.regenerate_answer is not None:
				regenerated = await self.regenerate_answer(query, refined_chunks)
				regenerated["corrective_labels"] = dict(counts)
				regenerated.setdefault("warnings", []).append("Corrective RAG regeneration applied.")
				return regenerated
			initial_result.setdefault("warnings", []).append("Corrective RAG requested but regenerate handler is unavailable.")
			return initial_result

		initial_result.setdefault("warnings", []).append("Corrective RAG check passed without re-retrieval.")
		return initial_result

	def classify_chunk(self, query: str, chunk: Chunk) -> str:
		q_terms = self._tokenize(query)
		c_terms = self._tokenize(chunk.text)
		overlap = len(q_terms & c_terms) / (len(q_terms) or 1)

		if overlap == 0:
			return "IRRELEVANT"

		if self._has_negation_conflict(query, chunk.text):
			return "CONTRADICTORY"

		if overlap >= 0.35:
			return "CORRECT"
		if overlap >= 0.15:
			return "AMBIGUOUS"
		return "INCORRECT"

	def _tokenize(self, text: str) -> set[str]:
		return {
			token
			for token in (part.strip(".,;:!?()[]{}\"'").lower() for part in text.split())
			if len(token) > 2 and token not in self._STOPWORDS
		}

	def _has_negation_conflict(self, query: str, chunk_text: str) -> bool:
		has_query_negation = any(tok in query.lower().split() for tok in {"no", "not", "never", "without"})
		has_chunk_negation = any(tok in chunk_text.lower().split() for tok in {"no", "not", "never", "without"})
		return has_query_negation != has_chunk_negation

	async def refine_knowledge(self, query: str, bad_chunks: list[Chunk]) -> list[Chunk]:
		if self.refine_retrieval is None:
			return []
		return await self.refine_retrieval(query, bad_chunks)


__all__ = ["CorrectiveRAG"]
