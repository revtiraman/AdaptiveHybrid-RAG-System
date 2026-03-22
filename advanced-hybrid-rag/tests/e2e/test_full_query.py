from __future__ import annotations

import io
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.main import create_app


def test_upload_and_query_full_flow():
	with TestClient(create_app()) as client:
		fake_pdf = io.BytesIO(b"%PDF-1.4 fake")
		upload = client.post("/api/ingest", files={"file": ("paper.pdf", fake_pdf, "application/pdf")})
		assert upload.status_code in (200, 500)

		query = client.post("/api/query", json={"query": "Summarize this", "mode": "auto", "filters": {}, "options": {}})
		assert query.status_code == 200
		assert "answer" in query.json()

