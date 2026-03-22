"""Query reformulation helpers for adaptive retrieval."""

from __future__ import annotations

import json
import re
from typing import Awaitable, Callable


class QueryReformulator:
	"""Generate alternative query forms for better retrieval coverage."""

	def __init__(self, llm_generate: Callable[[str], Awaitable[str]] | None = None) -> None:
		self.llm_generate = llm_generate

	async def expand_query(self, query: str) -> str:
		prompt = (
			"Expand this search query with related terms, synonyms, and alternative phrasings. "
			"Return only the expanded query, no explanation.\n"
			f"Query: {query}"
		)
		response = await self._safe_llm(prompt)
		return response or self._heuristic_expand(query)

	async def step_back(self, query: str) -> str:
		prompt = (
			"What is the more general question behind the following query? "
			"Return only the generalized question.\n"
			f"Query: {query}"
		)
		response = await self._safe_llm(prompt)
		return response or self._heuristic_step_back(query)

	async def generate_subqueries(self, query: str, n: int = 3) -> list[str]:
		prompt = (
			f"Generate {n} alternative search queries for the following question. "
			"Return as JSON with key sub_queries.\n"
			f"Question: {query}"
		)
		response = await self._safe_llm(prompt)
		parsed = self._parse_json_list(response, key="sub_queries")
		if parsed:
			return parsed[:n]

		base = self._heuristic_expand(query)
		variants = [query, base, self._heuristic_step_back(query)]
		return list(dict.fromkeys(v for v in variants if v))[:n]

	async def decompose_multihop(self, query: str) -> list[str]:
		prompt = (
			"Break this complex research question into 2-5 simpler sub-questions that can be "
			"answered independently. Return JSON {\"sub_questions\": [..]}.\n"
			f"Question: {query}"
		)
		response = await self._safe_llm(prompt)
		parsed = self._parse_json_list(response, key="sub_questions")
		if parsed:
			return parsed[:5]

		pieces = [p.strip().rstrip("?") + "?" for p in re.split(r"\band\b|,|;", query) if p.strip()]
		if len(pieces) < 2:
			return [query]
		return pieces[:5]

	async def _safe_llm(self, prompt: str) -> str:
		if self.llm_generate is None:
			return ""
		try:
			return (await self.llm_generate(prompt)).strip()
		except Exception:
			return ""

	def _parse_json_list(self, text: str, key: str) -> list[str]:
		if not text:
			return []
		try:
			data = json.loads(text)
			value = data.get(key)
			if isinstance(value, list):
				return [str(v).strip() for v in value if str(v).strip()]
		except Exception:
			return []
		return []

	def _heuristic_expand(self, query: str) -> str:
		additions = ["state of the art", "limitations", "comparison", "evaluation", "methodology"]
		return f"{query} {' '.join(additions)}"

	def _heuristic_step_back(self, query: str) -> str:
		return f"What broader research problem does this address: {query}?"


__all__ = ["QueryReformulator"]
