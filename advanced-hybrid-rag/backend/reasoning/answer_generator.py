"""Final answer synthesis using routing + citation annotation."""

from __future__ import annotations

import time
from uuid import uuid4

from ..ingestion.models import Chunk
from .citation_generator import CitationGenerator
from .llm_router import LLMRouter
from .query_analyzer import QueryAnalysis
from .structured_output import QueryResponse


class AnswerGenerator:
	"""Generate final answer with citations and response metadata."""

	def __init__(self, llm_router: LLMRouter | None = None, citation_generator: CitationGenerator | None = None) -> None:
		self.llm_router = llm_router or LLMRouter()
		self.citation_generator = citation_generator or CitationGenerator()

	async def generate(self, query: str, analysis: QueryAnalysis, chunks: list[Chunk], reasoning_trace: list[str] | None = None) -> QueryResponse:
		t0 = time.perf_counter()
		context = "\n\n".join(c.text for c in chunks[:8])
		messages = [
			{
				"role": "system",
				"content": "You are a research assistant. Answer with grounded statements and concise structure.",
			},
			{
				"role": "user",
				"content": f"Question: {query}\n\nContext:\n{context}",
			},
		]
		answer = await self.llm_router.generate(messages=messages, query_type=analysis.query_type, max_tokens=1200)
		answer_text = answer if isinstance(answer, str) else ""

		cited = self.citation_generator.generate_citations(answer=answer_text, retrieved_chunks=chunks, style="inline")
		latency_ms = (time.perf_counter() - t0) * 1000
		return QueryResponse(
			query_id=f"q-{uuid4().hex}",
			query=query,
			answer=cited.text_with_inline_cites,
			answer_summary=(answer_text[:180] + "...") if len(answer_text) > 180 else answer_text,
			answer_type=analysis.query_type,
			citations=cited.bibliography,
			sub_questions=None,
			reasoning_trace=reasoning_trace,
			confidence="MEDIUM",
			grounding_score=0.0,
			retrieval_quality=0.0,
			warnings=[],
			latency_ms=latency_ms,
			token_usage={},
			model_used=self.llm_router.select_model(analysis.query_type),
			corrective_iterations=0,
			cached=False,
		)


__all__ = ["AnswerGenerator"]
