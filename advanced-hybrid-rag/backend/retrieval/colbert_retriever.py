"""Approximate ColBERT late-interaction retrieval."""

from __future__ import annotations

import hashlib
import re

import numpy as np

from ..ingestion.models import Chunk
from ..storage.vector_store import SearchResult


class ColBERTRetriever:
	"""Token-level MaxSim scoring over an indexed candidate pool."""

	def __init__(self, dim: int = 64) -> None:
		self.dim = dim
		self._index: dict[str, tuple[Chunk, np.ndarray]] = {}

	def index_chunks(self, chunks: list[Chunk]) -> None:
		for chunk in chunks:
			token_emb = self._token_embeddings(chunk.text)
			self._index[chunk.metadata.chunk_id] = (chunk, token_emb)

	def search(self, query: str, k: int) -> list[SearchResult]:
		q_emb = self._token_embeddings(query)
		if q_emb.size == 0:
			return []
		scores: list[SearchResult] = []
		for _, (chunk, d_emb) in self._index.items():
			if d_emb.size == 0:
				continue
			sim = q_emb @ d_emb.T
			maxsim = sim.max(axis=1).sum()
			scores.append(SearchResult(chunk=chunk, score=float(maxsim), source="colbert"))
		scores.sort(key=lambda x: x.score, reverse=True)
		return scores[:k]

	def _token_embeddings(self, text: str) -> np.ndarray:
		tokens = re.findall(r"\w+", text.lower())
		if not tokens:
			return np.zeros((0, self.dim), dtype=np.float32)
		rows = [_stable_token_embedding(tok, self.dim) for tok in tokens]
		return np.vstack(rows)


def _stable_token_embedding(token: str, dim: int) -> np.ndarray:
	digest = hashlib.md5(token.encode("utf-8")).digest()
	seed = int.from_bytes(digest[:8], "big", signed=False)
	rng = np.random.default_rng(seed)
	vec = rng.standard_normal(dim).astype(np.float32)
	norm = np.linalg.norm(vec) or 1.0
	return vec / norm


__all__ = ["ColBERTRetriever"]
