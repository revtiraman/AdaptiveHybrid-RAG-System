from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.main import create_app


def test_feedback_submit_and_stats():
	with TestClient(create_app()) as client:
		resp = client.post(
			"/api/feedback/",
			json={
				"query_id": "q-1",
				"answer": "test",
				"rating": 2,
				"helpful": False,
				"bad_citation_ids": ["c1"],
			},
		)
		assert resp.status_code == 200
		assert resp.json()["status"] == "accepted"

		stats = client.get("/api/feedback/stats")
		assert stats.status_code == 200
		assert stats.json()["total_feedback"] >= 1


def test_annotations_create_and_list():
	with TestClient(create_app()) as client:
		payload = {
			"document_id": "doc-1",
			"chunk_id": "chunk-1",
			"note": "important paragraph",
			"label": "insight",
			"user_id": "u-1",
			"public": True,
		}
		create = client.post("/api/annotations", json=payload)
		assert create.status_code == 200

		listed = client.get("/api/annotations/doc-1")
		assert listed.status_code == 200
		items = listed.json()["annotations"]
		assert len(items) >= 1
		assert items[0]["label"] == "insight"


def test_planning_monitor_literature_and_analysis_endpoints():
	with TestClient(create_app()) as client:
		planning = client.post("/api/planning/react", json={"query": "How does this method compare?"})
		assert planning.status_code == 200
		assert "steps" in planning.json()

		config = client.post("/api/monitor/arxiv/config", json={"categories": ["cs.LG"], "keywords": ["rag"]})
		assert config.status_code == 200
		poll = client.post("/api/monitor/arxiv/poll")
		assert poll.status_code == 200
		assert poll.json()["count"] >= 1

		review = client.post(
			"/api/literature/review",
			json={
				"topic": "Hybrid RAG",
				"papers": [{"title": "Paper A", "summary": "Summary", "cluster": "methods"}],
			},
		)
		assert review.status_code == 200
		assert "Literature Review" in review.json()["review"]

		analysis = client.post(
			"/api/analysis/citations",
			json={"edges": [["paper-a", "paper-b"], ["paper-a", "paper-c"]]},
		)
		assert analysis.status_code == 200
		assert "metrics" in analysis.json()


def test_ingest_url_accepts_redact_pii_flag(monkeypatch):
	seen: dict[str, bool] = {"redact_pii": False}

	class DummyResult:
		def model_dump(self):
			return {
				"doc_id": "doc-test",
				"source_type": "url",
				"chunks_created": 1,
				"entities_extracted": 0,
				"ingestion_time_ms": 1.0,
				"warnings": [],
			}

	async def fake_ingest(*, source, source_type, redact_pii=True, metadata_override=None):
		_ = source
		_ = source_type
		_ = metadata_override
		seen["redact_pii"] = redact_pii
		return DummyResult()

	with TestClient(create_app()) as client:
		monkeypatch.setattr(client.app.state.pipeline, "ingest", fake_ingest)
		resp = client.post(
			"/api/ingest/url",
			json={"url": "https://example.com", "redact_pii": True},
		)
		assert resp.status_code == 200
		assert seen["redact_pii"] is True
