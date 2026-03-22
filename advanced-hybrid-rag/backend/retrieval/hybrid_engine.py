"""Hybrid retrieval orchestrator."""

from __future__ import annotations

import asyncio
import time
from collections import Counter

import numpy as np
from pydantic import BaseModel, Field

from ..ingestion.embedder import BaseEmbedder
from ..ingestion.models import Chunk
from ..storage.vector_store import SearchResult
from .bm25_retriever import BM25Retriever
from .colbert_retriever import ColBERTRetriever
from .fusion import RetrievalFusion
from .graph_retriever import GraphRetriever
from .hyde_retriever import HyDERetriever
from .reranker import CrossEncoderReranker
from .vector_retriever import VectorRetriever


class RetrievalFilters(BaseModel):
	paper_ids: list[str] = Field(default_factory=list)
	year_range: tuple[int, int] | None = None
	sections: list[str] = Field(default_factory=list)
	min_relevance: float = 0.0


class RetrievalResult(BaseModel):
	chunks: list[Chunk]
	retrieval_scores: dict[str, float]
	source_breakdown: dict[str, int]
	latency_ms: float


class HybridRetrievalEngine:
	"""Run and combine dense, sparse, graph, HyDE, and reranking retrieval."""

	def __init__(
		self,
		embedder: BaseEmbedder,
		vector_retriever: VectorRetriever,
		bm25_retriever: BM25Retriever,
		graph_retriever: GraphRetriever | None = None,
		hyde_retriever: HyDERetriever | None = None,
		colbert_retriever: ColBERTRetriever | None = None,
		reranker: CrossEncoderReranker | None = None,
		fusion: RetrievalFusion | None = None,
		k_vector: int = 30,
		k_bm25: int = 20,
		k_graph: int = 10,
		k_rerank_candidates: int = 50,
		rerank_threshold: float = 0.3,
	) -> None:
		self.embedder = embedder
		self.vector_retriever = vector_retriever
		self.bm25_retriever = bm25_retriever
		self.graph_retriever = graph_retriever
		self.hyde_retriever = hyde_retriever
		self.colbert_retriever = colbert_retriever
		self.reranker = reranker or CrossEncoderReranker(rerank_threshold=rerank_threshold)
		self.fusion = fusion or RetrievalFusion()
		self.k_vector = k_vector
		self.k_bm25 = k_bm25
		self.k_graph = k_graph
		self.k_rerank_candidates = k_rerank_candidates

	async def retrieve(
		self,
		query: str,
		query_embedding: np.ndarray,
		k_final: int,
		filters: RetrievalFilters,
		use_hyde: bool = False,
		use_graph: bool = True,
		use_colbert: bool = False,
	) -> RetrievalResult:
		start = time.perf_counter()

		tasks: list[tuple[str, object]] = [
			("vector", self.vector_retriever.retrieve(query_embedding=query_embedding, k=self.k_vector, filters=self._build_filter(filters))),
			("bm25", self.bm25_retriever.retrieve(query=query, k=self.k_bm25)),
		]

		if use_graph and self.graph_retriever is not None:
			tasks.append(("graph", self.graph_retriever.retrieve(query=query, k=self.k_graph)))
		if use_hyde and self.hyde_retriever is not None:
			tasks.append(("hyde", self.hyde_retriever.retrieve(query=query, k=self.k_vector)))

		raw_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
		results: list[list[SearchResult]] = []
		for (name, _), raw in zip(tasks, raw_results):
			if isinstance(raw, Exception):
				# Keep retrieval robust if one branch (e.g. graph backend) is unavailable.
				_ = name
				continue
			results.append(raw)
		fused = self.fusion.reciprocal_rank_fusion(results)
		filtered = self._apply_filters(fused, filters)
		diversified = self.fusion.enforce_diversity(filtered, max_per_doc=2)

		reranked = self.reranker.rerank(query=query, candidates=diversified[: self.k_rerank_candidates], top_k=max(k_final, 20))
		if use_colbert and self.colbert_retriever is not None and reranked:
			self.colbert_retriever.index_chunks([r.chunk for r in reranked])
			colbert_res = self.colbert_retriever.search(query=query, k=max(k_final, 20))
			reranked = self.fusion.reciprocal_rank_fusion([reranked, colbert_res])

		final = [r for r in reranked if r.score >= filters.min_relevance][:k_final]

		source_counts = Counter(r.source for r in final)
		latency_ms = (time.perf_counter() - start) * 1000
		return RetrievalResult(
			chunks=[r.chunk for r in final],
			retrieval_scores={r.chunk.metadata.chunk_id: r.score for r in final},
			source_breakdown=dict(source_counts),
			latency_ms=latency_ms,
		)

	def _apply_filters(self, items: list[SearchResult], filters: RetrievalFilters) -> list[SearchResult]:
		out: list[SearchResult] = []
		for item in items:
			md = item.chunk.metadata
			if filters.paper_ids and md.doc_id not in filters.paper_ids:
				continue
			if filters.sections and md.section not in filters.sections:
				continue
			out.append(item)
		return out

	def _build_filter(self, filters: RetrievalFilters) -> dict | None:
		if not filters.paper_ids:
			return None
		if len(filters.paper_ids) == 1:
			return {"doc_id": filters.paper_ids[0]}
		return None


__all__ = ["RetrievalFilters", "RetrievalResult", "HybridRetrievalEngine"]
