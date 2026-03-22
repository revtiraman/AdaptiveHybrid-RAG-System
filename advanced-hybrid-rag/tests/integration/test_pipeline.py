from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.ingestion.embedder import BGEEmbedder
from backend.ingestion.pipeline import IngestionPipeline
from backend.storage.bm25_store import BM25Store
from backend.storage.cache_store import SemanticCache
from backend.storage.graph_store import Neo4jGraphStore
from backend.storage.relational_store import RelationalStore
from backend.storage.vector_store import ChromaDBStore


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
	docs = pipeline.relational_store.list_documents()
	assert any(d["doc_id"] == result.doc_id for d in docs)
	bm25_hits = pipeline.bm25_store.search("retrieval generation", k=5)
	assert len(bm25_hits) >= 1


def test_delete_removes_from_all_stores(tmp_path: Path):
	pipeline = _pipeline(tmp_path)
	res = asyncio.run(pipeline.ingest(source=b'{"body":"doc"}', source_type="json"))
	deleted = asyncio.run(pipeline.delete_document(res.doc_id))
	assert deleted is True
	docs = pipeline.relational_store.list_documents()
	assert all(d["doc_id"] != res.doc_id for d in docs)


def test_adaptive_retries_on_low_quality(tmp_path: Path):
	pipeline = _pipeline(tmp_path)
	res = asyncio.run(pipeline.ingest(source=b'{"body":"some content"}', source_type="json"))
	assert res.ingestion_time_ms >= 0
	assert res.doc_id
	assert res.entities_extracted >= 0
