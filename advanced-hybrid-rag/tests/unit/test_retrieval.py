from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.ingestion.models import Chunk, ChunkMetadata
from backend.retrieval.hybrid_engine import HybridRetrievalEngine, RetrievalFilters
from backend.storage.vector_store import SearchResult


class _DummyEmbedder:
	def embed_query(self, text: str) -> np.ndarray:
		_ = text
		return np.ones(384, dtype=np.float32)


class _DummyVectorRetriever:
	async def retrieve(self, query_embedding: np.ndarray, k: int, filters: dict | None = None) -> list[SearchResult]:
		_ = query_embedding
		_ = k
		_ = filters
		return [_result("vector")]


class _DummyBM25Retriever:
	async def retrieve(self, query: str, k: int) -> list[SearchResult]:
		_ = query
		_ = k
		return [_result("bm25")]


class _CountingGraphRetriever:
	def __init__(self, should_fail: bool = False) -> None:
		self.calls = 0
		self.should_fail = should_fail

	async def retrieve(self, query: str, k: int) -> list[SearchResult]:
		_ = query
		_ = k
		self.calls += 1
		if self.should_fail:
			raise RuntimeError("graph backend unavailable")
		return [_result("graph")]


def _result(source: str) -> SearchResult:
	chunk = Chunk(
		text=f"{source} evidence",
		metadata=ChunkMetadata(
			doc_id=f"doc-{source}",
			chunk_id=f"chunk-{source}",
			source_file=source,
			section="s",
			page_start=1,
			page_end=1,
			char_start=0,
			char_end=10,
			chunk_index=0,
			total_chunks=1,
		),
	)
	return SearchResult(chunk=chunk, score=0.9, source=source)


def test_graph_retriever_called_when_enabled():
	graph = _CountingGraphRetriever()
	engine = HybridRetrievalEngine(
		embedder=_DummyEmbedder(),
		vector_retriever=_DummyVectorRetriever(),
		bm25_retriever=_DummyBM25Retriever(),
		graph_retriever=graph,
	)

	result = asyncio.run(
		engine.retrieve(
			query="graph query",
			query_embedding=np.ones(384, dtype=np.float32),
			k_final=3,
			filters=RetrievalFilters(),
			use_graph=True,
		)
	)

	assert graph.calls == 1
	assert result.source_breakdown


def test_graph_retriever_not_called_when_disabled():
	graph = _CountingGraphRetriever()
	engine = HybridRetrievalEngine(
		embedder=_DummyEmbedder(),
		vector_retriever=_DummyVectorRetriever(),
		bm25_retriever=_DummyBM25Retriever(),
		graph_retriever=graph,
	)

	_ = asyncio.run(
		engine.retrieve(
			query="graph query",
			query_embedding=np.ones(384, dtype=np.float32),
			k_final=3,
			filters=RetrievalFilters(),
			use_graph=False,
		)
	)

	assert graph.calls == 0


def test_graph_failure_does_not_break_retrieval():
	graph = _CountingGraphRetriever(should_fail=True)
	engine = HybridRetrievalEngine(
		embedder=_DummyEmbedder(),
		vector_retriever=_DummyVectorRetriever(),
		bm25_retriever=_DummyBM25Retriever(),
		graph_retriever=graph,
	)

	result = asyncio.run(
		engine.retrieve(
			query="graph query",
			query_embedding=np.ones(384, dtype=np.float32),
			k_final=3,
			filters=RetrievalFilters(),
			use_graph=True,
		)
	)

	assert graph.calls == 1
	assert result.latency_ms >= 0
