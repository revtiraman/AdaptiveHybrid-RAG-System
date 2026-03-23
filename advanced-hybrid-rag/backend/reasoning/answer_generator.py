"""Final answer synthesis using routing + citation annotation."""

from __future__ import annotations

import logging
import re
import time
from uuid import uuid4

from ..config.prompts import SYNTHESIS_PROMPT
from ..ingestion.models import Chunk
from .citation_generator import CitationGenerator
from .llm_router import LLMRouter
from .query_analyzer import QueryAnalysis
from .structured_output import QueryResponse


logger = logging.getLogger(__name__)


class AnswerGenerationError(RuntimeError):
	"""Raised when LLM answer generation fails."""


class AnswerGenerator:
	"""Generate final answer with citations and response metadata."""

	def __init__(self, llm_router: LLMRouter | None = None, citation_generator: CitationGenerator | None = None) -> None:
		self.llm_router = llm_router or LLMRouter()
		self.citation_generator = citation_generator or CitationGenerator()

	async def generate(self, query: str, analysis: QueryAnalysis, chunks: list[Chunk], reasoning_trace: list[str] | None = None) -> QueryResponse:
		t0 = time.perf_counter()
		usable_chunks = filter_reference_chunks(chunks)
		if not usable_chunks:
			usable_chunks = chunks

		context = "\n\n".join(
			f"[{c.metadata.chunk_id}] {c.text.strip()}" for c in usable_chunks[:8] if c.text.strip()
		)
		prompt = SYNTHESIS_PROMPT.format(query=query, context=context)
		model = self.llm_router.select_model(analysis.query_type)
		logger.debug(
			"LLM call | model=%s | prompt_tokens≈%d | context_chunks=%d",
			model,
			len(prompt) // 4,
			len(usable_chunks),
		)
		messages = [
			{
				"role": "system",
				"content": "You are a precise scientific assistant.",
			},
			{
				"role": "user",
				"content": prompt,
			},
		]

		try:
			answer = await self.llm_router.generate(messages=messages, query_type=analysis.query_type, max_tokens=1200)
			answer_text = answer if isinstance(answer, str) else ""
			logger.debug("LLM response | length=%d | first_100=%r", len(answer_text), answer_text[:100])
			if answer_text.startswith("LLM fallback response:"):
				raise AnswerGenerationError("LLM router returned fallback text instead of synthesized answer")
		except Exception as e:
			logger.error("LLM generation failed: %s", e, exc_info=True)
			raise AnswerGenerationError(f"LLM call failed: {e}") from e

		if is_raw_echo(answer_text, usable_chunks):
			logger.error("Detected raw echo in generated answer, attempting regeneration with strict anti-copy instruction.")
			messages[0]["content"] = (
				"DO NOT COPY ANY SENTENCE VERBATIM FROM CONTEXT. "
				"Paraphrase in your own words and provide concise synthesis only."
			)
			try:
				second = await self.llm_router.generate(messages=messages, query_type=analysis.query_type, max_tokens=1200)
				second_text = second if isinstance(second, str) else ""
				logger.debug("LLM response (retry) | length=%d | first_100=%r", len(second_text), second_text[:100])
				if second_text and not second_text.startswith("LLM fallback response:"):
					answer_text = second_text
			except Exception as e:
				logger.error("LLM regeneration failed after raw-echo detection: %s", e, exc_info=True)

		cited = self.citation_generator.generate_citations(answer=answer_text, retrieved_chunks=usable_chunks, style="inline")
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


def filter_reference_chunks(chunks: list[Chunk]) -> list[Chunk]:
	reference_pattern = re.compile(r"^\s*\[\d+\]|\bet\s+al\b|doi:|arxiv:", re.I)
	return [c for c in chunks if not reference_pattern.search((c.text or "")[:200])]


def longest_common_substring(a: str, b: str) -> str:
	a = (a or "")[:4000]
	b = (b or "")[:4000]
	if not a or not b:
		return ""
	prev = [0] * (len(b) + 1)
	best_len = 0
	best_end = 0
	for i, ca in enumerate(a, start=1):
		curr = [0]
		for j, cb in enumerate(b, start=1):
			if ca == cb:
				val = prev[j - 1] + 1
				curr.append(val)
				if val > best_len:
					best_len = val
					best_end = i
			else:
				curr.append(0)
		prev = curr
	return a[best_end - best_len : best_end]


def is_raw_echo(answer: str, chunks: list[Chunk]) -> bool:
	for chunk in chunks:
		overlap = longest_common_substring(answer, chunk.text)
		if len(overlap) > 80:
			return True
	return False


__all__ = [
	"AnswerGenerator",
	"AnswerGenerationError",
	"filter_reference_chunks",
	"longest_common_substring",
	"is_raw_echo",
]
