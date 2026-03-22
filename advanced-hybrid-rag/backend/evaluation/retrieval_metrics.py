"""Retrieval metrics and embedding drift detection."""

from __future__ import annotations

import math

import numpy as np


def precision_at_k(relevant: set, retrieved: list, k: int) -> float:
	if k <= 0:
		return 0.0
	top = retrieved[:k]
	hits = sum(1 for item in top if item in relevant)
	return hits / k


def recall_at_k(relevant: set, retrieved: list, k: int) -> float:
	if not relevant:
		return 0.0
	top = retrieved[:k]
	hits = sum(1 for item in top if item in relevant)
	return hits / len(relevant)


def mean_reciprocal_rank(relevant: set, retrieved: list) -> float:
	for i, item in enumerate(retrieved, start=1):
		if item in relevant:
			return 1.0 / i
	return 0.0


def ndcg_at_k(relevance_scores: list[int], k: int) -> float:
	top = relevance_scores[:k]
	dcg = sum((rel / math.log2(i + 2)) for i, rel in enumerate(top))
	ideal = sorted(relevance_scores, reverse=True)[:k]
	idcg = sum((rel / math.log2(i + 2)) for i, rel in enumerate(ideal))
	return (dcg / idcg) if idcg else 0.0


def mean_average_precision(relevant: set, retrieved: list) -> float:
	if not relevant:
		return 0.0
	precisions = []
	hit_count = 0
	for i, item in enumerate(retrieved, start=1):
		if item in relevant:
			hit_count += 1
			precisions.append(hit_count / i)
	return sum(precisions) / len(relevant) if precisions else 0.0


class EmbeddingDriftDetector:
	"""Track embedding distribution drift with MMD-style statistic."""

	def __init__(self, threshold: float = 0.2) -> None:
		self.threshold = threshold

	def compute_mmd(self, base: np.ndarray, new: np.ndarray) -> float:
		if base.size == 0 or new.size == 0:
			return 0.0
		x = np.atleast_2d(base)
		y = np.atleast_2d(new)
		k_xx = self._rbf_kernel(x, x).mean()
		k_yy = self._rbf_kernel(y, y).mean()
		k_xy = self._rbf_kernel(x, y).mean()
		return float(max(0.0, k_xx + k_yy - 2 * k_xy))

	def has_drift(self, base: np.ndarray, new: np.ndarray) -> bool:
		return self.compute_mmd(base, new) > self.threshold

	def _rbf_kernel(self, a: np.ndarray, b: np.ndarray, gamma: float = 1.0) -> np.ndarray:
		dist_sq = ((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2)
		return np.exp(-gamma * dist_sq)


__all__ = [
	"precision_at_k",
	"recall_at_k",
	"mean_reciprocal_rank",
	"ndcg_at_k",
	"mean_average_precision",
	"EmbeddingDriftDetector",
]
