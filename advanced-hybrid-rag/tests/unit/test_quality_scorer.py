from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from adaptive.quality_scorer import RetrievalQualityScorer
from ingestion.models import Chunk, ChunkMetadata


def _chunk(doc_id: str, text: str, emb: list[float]) -> Chunk:
    return Chunk(
        text=text,
        metadata=ChunkMetadata(
            doc_id=doc_id,
            chunk_id=f"{doc_id}-{abs(hash(text))}",
            source_file="src",
            section="s",
            page_start=1,
            page_end=1,
            char_start=0,
            char_end=len(text),
            chunk_index=0,
            total_chunks=1,
        ),
        embedding=emb,
    )


def test_relevance_score_range_0_to_1():
    scorer = RetrievalQualityScorer()
    chunks = [_chunk("d1", "bert model", [1, 0, 0]), _chunk("d2", "gpt model", [0, 1, 0])]
    m = scorer.score("bert", np.array([1.0, 0.0, 0.0]), chunks)
    assert 0.0 <= m.relevance_score <= 1.0


def test_diversity_low_when_single_doc():
    scorer = RetrievalQualityScorer()
    chunks = [_chunk("d1", "a b c", [1, 0, 0]), _chunk("d1", "d e f", [0.9, 0.1, 0])]
    m = scorer.score("a", np.array([1.0, 0.0, 0.0]), chunks)
    assert m.diversity_score < 0.8


def test_coverage_penalizes_missing_keywords():
    scorer = RetrievalQualityScorer()
    chunks = [_chunk("d1", "transformer architecture", [1, 0, 0])]
    m = scorer.score("graph retrieval and reranking", np.array([1.0, 0.0, 0.0]), chunks)
    assert m.coverage_score < 0.8
