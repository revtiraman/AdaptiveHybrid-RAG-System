"""Semantic response cache backed by Redis with in-memory fallback."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class CachedResponse:
	query: str
	response: dict[str, Any]
	similarity: float
	created_at: float
	ttl_seconds: int
	doc_ids: list[str]


class SemanticCache:
	"""Cache query responses by embedding similarity."""

	def __init__(self, redis_url: str, threshold: float = 0.92, ttl_seconds: int = 3600):
		self.redis_url = redis_url
		self.threshold = threshold
		self.ttl_seconds = ttl_seconds
		self._redis = None
		self._memory: dict[str, dict[str, Any]] = {}

	async def get(self, query: str, query_embedding: np.ndarray) -> CachedResponse | None:
		now = time.time()
		entries = await self._all_entries()
		best_key = None
		best_sim = -1.0
		for key, item in entries.items():
			created = float(item.get("created_at", 0))
			ttl = int(item.get("ttl_seconds", self.ttl_seconds))
			if created + ttl < now:
				continue
			emb = np.asarray(item.get("embedding", []), dtype=np.float32)
			sim = _cosine(query_embedding, emb)
			if sim > best_sim:
				best_sim = sim
				best_key = key
		if best_key is None or best_sim < self.threshold:
			return None

		item = entries[best_key]
		return CachedResponse(
			query=item["query"],
			response=item["response"],
			similarity=best_sim,
			created_at=float(item["created_at"]),
			ttl_seconds=int(item["ttl_seconds"]),
			doc_ids=list(item.get("doc_ids", [])),
		)

	async def set(self, query: str, query_embedding: np.ndarray, response: Any) -> None:
		payload = {
			"query": query,
			"embedding": query_embedding.astype(float).tolist(),
			"response": response.model_dump() if hasattr(response, "model_dump") else response,
			"created_at": time.time(),
			"ttl_seconds": self.ttl_seconds,
			"doc_ids": _extract_doc_ids(response),
		}
		key = f"cache:{abs(hash(query))}"

		redis = await self._get_redis()
		if redis is None:
			self._memory[key] = payload
			return
		await redis.set(key, json.dumps(payload), ex=self.ttl_seconds)

	async def invalidate_by_doc(self, doc_id: str) -> int:
		removed = 0
		redis = await self._get_redis()
		if redis is None:
			keys = [k for k, v in self._memory.items() if doc_id in v.get("doc_ids", [])]
			for key in keys:
				self._memory.pop(key, None)
				removed += 1
			return removed

		keys = await redis.keys("cache:*")
		for key in keys:
			raw = await redis.get(key)
			if not raw:
				continue
			payload = json.loads(raw)
			if doc_id in payload.get("doc_ids", []):
				await redis.delete(key)
				removed += 1
		return removed

	async def _get_redis(self):
		if self._redis is not None:
			return self._redis
		try:
			import redis.asyncio as redis

			self._redis = redis.from_url(self.redis_url, decode_responses=True)
			await self._redis.ping()
			return self._redis
		except Exception:
			return None

	async def _all_entries(self) -> dict[str, dict[str, Any]]:
		redis = await self._get_redis()
		if redis is None:
			return self._memory
		out: dict[str, dict[str, Any]] = {}
		for key in await redis.keys("cache:*"):
			raw = await redis.get(key)
			if raw:
				out[str(key)] = json.loads(raw)
		return out


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
	if a.size == 0 or b.size == 0:
		return 0.0
	a = a.reshape(-1)
	b = b.reshape(-1)
	denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
	return float(np.dot(a, b) / denom)


def _extract_doc_ids(response: Any) -> list[str]:
	if hasattr(response, "citations"):
		citations = getattr(response, "citations", [])
		ids = [getattr(c, "doc_id", None) for c in citations]
		return [x for x in ids if x]
	if isinstance(response, dict) and isinstance(response.get("citations"), list):
		return [c.get("doc_id") for c in response["citations"] if c.get("doc_id")]
	return []


__all__ = ["SemanticCache", "CachedResponse"]
