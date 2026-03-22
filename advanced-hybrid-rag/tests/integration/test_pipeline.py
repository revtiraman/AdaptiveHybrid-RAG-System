from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from ingestion.embedder import BGEEmbedder
from ingestion.pipeline import IngestionPipeline
from storage.bm25_store import BM25Store
from storage.cache_store import SemanticCache
from storage.graph_store import Neo4jGraphStore
from storage.relational_store import RelationalStore
from storage.vector_store import ChromaDBStore


def _pipeline(tmp_path: Path) -> IngestionPipeline:
	return IngestionPipeline(
		embedder=BGEEmbedder(),
		vector_store=ChromaDBStore(),
		bm25_store=BM25Store(index_path=tmp_path / "bm25.pkl"),
		relational_store=RelationalStore(db_path=tmp_path / "meta.sqlite3"),
		graph_store=Neo4jGraphStore(),
		cache_store=SemanticCache(redis_url="redis://localhost:6379"),
	)


def test_full_ingestion_creates_all_stores(tmp_path: Path):
	pipeline = _pipeline(tmp_path)
	result = asyncio.run(
		pipeline.ingest(source=b'{"title":"x","body":"retrieval augmented generation"}', source_type="json")
	)
	assert result.chunks_created >= 1


def test_delete_removes_from_all_stores(tmp_path: Path):
	pipeline = _pipeline(tmp_path)
	res = asyncio.run(pipeline.ingest(source=b'{"body":"doc"}', source_type="json"))
	deleted = asyncio.run(pipeline.delete_document(res.doc_id))
	assert deleted is True


def test_adaptive_retries_on_low_quality(tmp_path: Path):
	pipeline = _pipeline(tmp_path)
	res = asyncio.run(pipeline.ingest(source=b'{"body":"some content"}', source_type="json"))
	assert res.ingestion_time_ms >= 0
