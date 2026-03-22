"""Cross-encoder reranking over retrieval candidates."""

from __future__ import annotations

from typing import Iterable

from ..storage.vector_store import SearchResult


class CrossEncoderReranker:
	"""Rerank candidate chunks using a cross-encoder or lexical fallback."""

	def __init__(self, rerank_threshold: float = 0.3, batch_size: int = 16) -> None:
		self.rerank_threshold = rerank_threshold
		self.batch_size = batch_size
		self.primary_model_name = "BAAI/bge-reranker-v2-m3"
		self.fallback_model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
		self._model = None
		self._load_attempted = False
		self._cache: dict[tuple[str, str], float] = {}

	def rerank(self, query: str, candidates: list[SearchResult], top_k: int = 5) -> list[SearchResult]:
		if not candidates:
			return []

		pairs = [(query, c.chunk.text) for c in candidates]
		scores = self._predict_scores(pairs)
		reranked: list[SearchResult] = []
		for candidate, score in zip(candidates, scores):
			if score >= self.rerank_threshold:
				reranked.append(SearchResult(chunk=candidate.chunk, score=float(score), source="rerank"))
		reranked.sort(key=lambda x: x.score, reverse=True)
		return reranked[:top_k]

	def _predict_scores(self, pairs: list[tuple[str, str]]) -> list[float]:
		out: list[float] = []
		missing: list[tuple[int, tuple[str, str]]] = []
		for idx, pair in enumerate(pairs):
			if pair in self._cache:
				out.append(self._cache[pair])
			else:
				out.append(0.0)
				missing.append((idx, pair))

		if missing:
			for batch in _batched(missing, self.batch_size):
				indices = [i for i, _ in batch]
				batch_pairs = [p for _, p in batch]
				model = self._get_model()
				if model is not None:
					batch_scores = model.predict(batch_pairs).tolist()
				else:
					batch_scores = [self._lexical_score(q, t) for q, t in batch_pairs]
				for idx, pair, score in zip(indices, batch_pairs, batch_scores):
					out[idx] = float(score)
					self._cache[pair] = float(score)
		return out

	def _get_model(self):
		if self._load_attempted:
			return self._model
		self._load_attempted = True
		self._model = self._load_model(self.primary_model_name) or self._load_model(self.fallback_model_name)
		return self._model

	def _load_model(self, model_name: str):
		try:
			from sentence_transformers import CrossEncoder

			return CrossEncoder(model_name)
		except Exception:
			return None

	def _lexical_score(self, query: str, text: str) -> float:
		q = set(query.lower().split())
		t = set(text.lower().split())
		denom = len(q | t) or 1
		return len(q & t) / denom


def _batched(values: list[tuple[int, tuple[str, str]]], batch_size: int) -> Iterable[list[tuple[int, tuple[str, str]]]]:
	for i in range(0, len(values), batch_size):
		yield values[i : i + batch_size]


__all__ = ["CrossEncoderReranker"]
