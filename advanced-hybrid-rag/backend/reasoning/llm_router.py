"""LLM routing across providers/models with fallback logic."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import AsyncGenerator


class LLMRouter:
	"""Route generation requests to best-fit model/provider."""

	def __init__(self, temperature: float = 0.1) -> None:
		self.temperature = temperature
		self.fail_counts: dict[str, int] = defaultdict(int)
		self.latency_ms: dict[str, list[float]] = defaultdict(list)

	def select_model(self, query_type: str) -> str:
		if query_type in {"simple_fact", "procedural"}:
			return "gpt-4o-mini"
		if query_type in {"multi_hop", "causal", "comparative"}:
			return "gpt-4o"
		if query_type == "survey":
			return "claude-3-5-sonnet"
		return "gpt-4o-mini"

	async def generate(
		self,
		messages: list[dict],
		query_type: str,
		max_tokens: int,
		stream: bool = False,
	) -> str | AsyncGenerator[str, None]:
		model = self.select_model(query_type)
		if self.fail_counts.get(model, 0) >= 3:
			model = "ollama/llama3"

		start = time.perf_counter()
		try:
			try:
				import litellm

				response = await litellm.acompletion(
					model=model,
					messages=messages,
					max_tokens=max_tokens,
					temperature=self.temperature,
					stream=stream,
				)
				if stream:
					async def _stream():
						async for chunk in response:
							delta = chunk.choices[0].delta.content or ""
							if delta:
								yield delta
					return _stream()
				text = response.choices[0].message.content or ""
			except Exception:
				text = self._fallback_text(messages)

			elapsed = (time.perf_counter() - start) * 1000
			self.latency_ms[model].append(elapsed)
			self.fail_counts[model] = 0
			return text
		except Exception:
			self.fail_counts[model] += 1
			return self._fallback_text(messages)

	def _fallback_text(self, messages: list[dict]) -> str:
		user_parts = [m.get("content", "") for m in messages if m.get("role") == "user"]
		content = " ".join(user_parts).strip()
		return f"LLM fallback response: {content[:1000]}"


__all__ = ["LLMRouter"]
