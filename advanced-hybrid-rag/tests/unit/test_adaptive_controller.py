from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.adaptive.adaptive_controller import AdaptiveRetrievalController
from backend.adaptive.quality_scorer import QualityMetrics
from backend.ingestion.models import Chunk, ChunkMetadata
from backend.retrieval.hybrid_engine import RetrievalResult


def _chunk(chunk_id: str = "c1") -> Chunk:
	return Chunk(
		text="retrieval evidence",
		metadata=ChunkMetadata(
			doc_id="d1",
			chunk_id=chunk_id,
			source_file="src",
			section="method",
			page_start=1,
			page_end=1,
			char_start=0,
			char_end=10,
			chunk_index=0,
			total_chunks=1,
		),
	)


def test_should_retry_true_for_low_relevance_quality():
	ctl = AdaptiveRetrievalController(settings=SimpleNamespace(quality_threshold=0.65, max_corrective_retries=3))
	assert ctl.should_retry(quality_score=0.2, attempt=0)
	assert ctl.should_retry(quality_score="Low", attempt=1)


def test_optimize_retrieval_increases_k_vector_for_low_relevance():
	ctl = AdaptiveRetrievalController(settings=SimpleNamespace(quality_threshold=0.65, max_corrective_retries=3))
	initial = RetrievalResult(chunks=[_chunk()], retrieval_scores={"c1": 0.2}, source_breakdown={"vector": 1}, latency_ms=10.0)
	quality = QualityMetrics(
		relevance_score=0.2,
		diversity_score=0.7,
		coverage_score=0.6,
		completeness_score=0.8,
		overall_quality=0.45,
		issues=["low_relevance"],
	)

	params = asyncio.run(ctl.optimize_retrieval(query="test query", initial_results=initial, quality=quality, attempt=1))
	assert params.k_vector > 30
