from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class _FakePaper:
    def __init__(self, title: str) -> None:
        self.title = title


class _FakeMetadataStore:
    def get_paper(self, paper_id: str):
        if paper_id == "paper-1":
            return _FakePaper("Demo Paper")
        return None

    def fetch_chunk_samples(self, paper_id: str, limit: int = 5):
        _ = paper_id
        return [
            {
                "chunk_id": "c1",
                "paper_id": "paper-1",
                "page_number": 1,
                "section": "intro",
                "ordinal": 0,
                "text_preview": "sample",
                "char_count": 6,
                "claim_count": 1,
                "looks_like_reference": False,
                "looks_like_noise": False,
            }
        ][:limit]


class _FakeSystem:
    def __init__(self) -> None:
        self.metadata_store = _FakeMetadataStore()

    def stats(self):
        class _S:
            papers = 1
            chunks = 1
            embedding_provider = "test"
            reranker_provider = "test"
            llm_provider = "none"

        return _S()

    def list_papers(self):
        return []


class _FakeContainer:
    def __init__(self) -> None:
        self.system = _FakeSystem()
        self.settings = type("S", (), {"documents_dir": Path("/tmp")})()


class ApiDebugRouteTests(unittest.TestCase):
    def test_debug_chunk_sample_route(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError:
            self.skipTest("FastAPI test dependencies are not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            original_env = dict(os.environ)
            try:
                os.environ["APP_ROOT_DIR"] = tmpdir
                os.environ["RAG_DATA_DIR"] = "data"
                os.environ["RAG_SQLITE_PATH"] = "meta.sqlite3"
                os.environ["RAG_CHROMA_PATH"] = "chroma"

                with patch("research_rag.api.app.build_container", return_value=_FakeContainer()):
                    from research_rag.api.app import create_app

                    client = TestClient(create_app())
                    resp = client.post("/debug/chunk-sample", json={"paper_id": "paper-1", "limit": 1})
                    self.assertEqual(resp.status_code, 200)
                    body = resp.json()
                    self.assertEqual(body["paper_id"], "paper-1")
                    self.assertEqual(body["sample_count"], 1)
                    self.assertEqual(body["chunks"][0]["chunk_id"], "c1")
            finally:
                os.environ.clear()
                os.environ.update(original_env)


if __name__ == "__main__":
    unittest.main()
