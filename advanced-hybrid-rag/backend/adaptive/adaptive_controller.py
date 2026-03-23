"""Adaptive retrieval controller."""

from __future__ import annotations

from types import SimpleNamespace

from pydantic import BaseModel

from ..retrieval.hybrid_engine import RetrievalResult
from .quality_scorer import QualityMetrics
from .query_reformulator import QueryReformulator


class RetrievalParameters(BaseModel):
	query: str
	k_vector: int = 30
	k_bm25: int = 20
	k_graph: int = 10
	use_hyde: bool = False
	use_graph: bool = True
	use_colbert: bool = False
	max_per_doc: int = 2
	rerank_threshold: float = 0.3


class AdaptiveRetrievalController:
	"""Tune retrieval parameters based on quality diagnostics."""

	def __init__(self, reformulator: QueryReformulator | None = None, settings: object | None = None) -> None:
		self.reformulator = reformulator or QueryReformulator()
		self.settings = settings or SimpleNamespace(quality_threshold=0.65, max_corrective_retries=3)

	async def optimize_retrieval(
		self,
		query: str,
		initial_results: RetrievalResult,
		quality: QualityMetrics,
		attempt: int,
	) -> RetrievalParameters:
		params = RetrievalParameters(query=query)

		if quality.relevance_score < 0.4:
			params.k_vector = int(params.k_vector * 1.5)
			params.use_hyde = True
			params.rerank_threshold = max(0.05, params.rerank_threshold * 0.8)

		if quality.diversity_score < 0.35:
			params.max_per_doc = 1
			params.use_graph = True

		if quality.coverage_score < 0.45:
			params.k_bm25 = int(params.k_bm25 * 1.5)
			params.query = await self.reformulator.expand_query(query)

		if attempt >= 2:
			params.use_colbert = True

		if initial_results.chunks and quality.overall_quality >= 0.75:
			params.k_vector = max(10, int(params.k_vector * 0.8))
			params.k_bm25 = max(10, int(params.k_bm25 * 0.8))

		return params

	def should_retry(self, quality_score: float | str, attempt: int) -> bool:
		if isinstance(quality_score, str):
			quality_score = {"High": 0.85, "Medium": 0.60, "Low": 0.30}.get(quality_score, 0.30)

		threshold = float(getattr(self.settings, "quality_threshold", 0.65) or 0.65)
		max_retries = int(getattr(self.settings, "max_corrective_retries", 3) or 3)

		return float(quality_score) < threshold and attempt < max_retries


__all__ = ["RetrievalParameters", "AdaptiveRetrievalController"]
