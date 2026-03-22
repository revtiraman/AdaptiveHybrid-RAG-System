from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from main import create_app


def test_health_endpoint():
	app = create_app()
	client = TestClient(app)
	resp = client.get("/api/health")
	assert resp.status_code == 200
	assert resp.json()["status"] == "ok"


def test_query_returns_valid_response_structure():
	app = create_app()
	client = TestClient(app)
	body = {"query": "What is RAG?", "mode": "auto", "filters": {}, "options": {}}
	resp = client.post("/api/query", json=body)
	assert resp.status_code == 200
	payload = resp.json()
	assert "answer" in payload
	assert "query" in payload

