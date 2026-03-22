from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from ingestion.models import Chunk, ChunkMetadata
from retrieval.fusion import RetrievalFusion
from storage.vector_store import SearchResult


def _res(doc: str, chunk_id: str, score: float) -> SearchResult:
	return SearchResult(
		chunk=Chunk(
			text=f"text-{chunk_id}",
			metadata=ChunkMetadata(
				doc_id=doc,
				chunk_id=chunk_id,
				source_file="s",
				section="sec",
				page_start=1,
				page_end=1,
				char_start=0,
				char_end=10,
				chunk_index=0,
				total_chunks=1,
			),
		),
		score=score,
	)


def test_rrf_correct_formula():
	f = RetrievalFusion()
	a = [_res("d1", "c1", 1.0), _res("d2", "c2", 0.8)]
	b = [_res("d2", "c2", 1.0), _res("d1", "c1", 0.8)]
	out = f.reciprocal_rank_fusion([a, b], k=60)
	assert len(out) == 2


def test_rrf_deduplicates():
	f = RetrievalFusion()
	out = f.reciprocal_rank_fusion([[_res("d1", "c1", 1.0)], [_res("d1", "c1", 0.5)]])
	assert len(out) == 1


def test_diversity_enforcement_caps_per_doc():
	f = RetrievalFusion()
	results = [_res("d1", f"c{i}", 1.0 - i * 0.1) for i in range(5)] + [_res("d2", "cx", 0.7)]
	out = f.enforce_diversity(results, max_per_doc=1)
	docs = [r.chunk.metadata.doc_id for r in out]
	assert docs.count("d1") <= 1


def test_weighted_combination_sums_to_one():
	f = RetrievalFusion()
	out = f.weighted_combination([_res("d1", "c1", 1.0)], [_res("d2", "c2", 1.0)], alpha=0.6)
	assert out
	assert all(0.0 <= r.score <= 1.0 for r in out)
