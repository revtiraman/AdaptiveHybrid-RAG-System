"""Hybrid retrieval fusion and diversity utilities."""

from __future__ import annotations

import math
from collections import defaultdict

from ..storage.vector_store import SearchResult


class RetrievalFusion:
	"""Fuse and diversify retrieval outputs from multiple retrievers."""

	def reciprocal_rank_fusion(
		self,
		result_lists: list[list[SearchResult]],
		k: int = 60,
		weights: list[float] | None = None,
	) -> list[SearchResult]:
		if not result_lists:
			return []
		if weights is None:
			weights = [1.0] * len(result_lists)

		score_map: dict[str, float] = defaultdict(float)
		best_item: dict[str, SearchResult] = {}
		for list_idx, results in enumerate(result_lists):
			weight = weights[list_idx] if list_idx < len(weights) else 1.0
			for rank, item in enumerate(results, start=1):
				key = item.chunk.metadata.chunk_id
				score_map[key] += weight * (1.0 / (k + rank))
				if key not in best_item or item.score > best_item[key].score:
					best_item[key] = item

		merged = []
		for key, item in best_item.items():
			merged.append(SearchResult(chunk=item.chunk, score=score_map[key], source=item.source))
		merged.sort(key=lambda x: x.score, reverse=True)
		return merged

	def weighted_combination(
		self,
		vector_results: list[SearchResult],
		bm25_results: list[SearchResult],
		alpha: float = 0.6,
	) -> list[SearchResult]:
		vec_norm = self._normalize_scores(vector_results)
		bm_norm = self._normalize_scores(bm25_results)
		merged: dict[str, SearchResult] = {}

		for item in vec_norm:
			key = item.chunk.metadata.chunk_id
			merged[key] = SearchResult(chunk=item.chunk, score=alpha * item.score, source="vector")
		for item in bm_norm:
			key = item.chunk.metadata.chunk_id
			if key in merged:
				merged[key].score += (1.0 - alpha) * item.score
			else:
				merged[key] = SearchResult(chunk=item.chunk, score=(1.0 - alpha) * item.score, source="bm25")
		out = list(merged.values())
		out.sort(key=lambda x: x.score, reverse=True)
		return out

	def enforce_diversity(self, results: list[SearchResult], max_per_doc: int = 2) -> list[SearchResult]:
		if not results:
			return []
		selected: list[SearchResult] = []
		doc_count: dict[str, int] = defaultdict(int)
		lambda_mmr = 0.7

		candidates = results[:]
		while candidates:
			best_idx = 0
			best_val = -math.inf
			for idx, cand in enumerate(candidates):
				doc_id = cand.chunk.metadata.doc_id
				if doc_count[doc_id] >= max_per_doc:
					continue
				novelty = 1.0 - max((self._text_similarity(cand, s) for s in selected), default=0.0)
				mmr = lambda_mmr * cand.score + (1.0 - lambda_mmr) * novelty
				if mmr > best_val:
					best_val = mmr
					best_idx = idx
			chosen = candidates.pop(best_idx)
			if doc_count[chosen.chunk.metadata.doc_id] >= max_per_doc:
				continue
			selected.append(chosen)
			doc_count[chosen.chunk.metadata.doc_id] += 1
		return selected

	def _normalize_scores(self, results: list[SearchResult]) -> list[SearchResult]:
		if not results:
			return []
		vals = [r.score for r in results]
		lo, hi = min(vals), max(vals)
		if hi == lo:
			return [SearchResult(chunk=r.chunk, score=1.0, source=r.source) for r in results]
		return [SearchResult(chunk=r.chunk, score=(r.score - lo) / (hi - lo), source=r.source) for r in results]

	def _text_similarity(self, a: SearchResult, b: SearchResult) -> float:
		ta = set(a.chunk.text.lower().split())
		tb = set(b.chunk.text.lower().split())
		denom = len(ta | tb) or 1
		return len(ta & tb) / denom


__all__ = ["RetrievalFusion"]
