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


class _FakeSystem:
    def __init__(self) -> None:
        self.calls = []

    def arxiv_sync(self, **kwargs):
        self.calls.append(kwargs)
        return {"ok": True, "query": kwargs["query"], "dry_run": kwargs["dry_run"]}

    def stats(self):
        class _S:
            papers = 0
            chunks = 0
            embedding_provider = "test"
            reranker_provider = "test"
            llm_provider = "none"

        return _S()

    def list_papers(self):
        return []


class _FakeContainer:
    def __init__(self) -> None:
        self.system = _FakeSystem()
        self.settings = type(
            "S",
            (),
            {
                "documents_dir": Path("/tmp"),
                "arxiv_default_query": "rag",
                "arxiv_max_results": 7,
                "arxiv_days_back": 21,
                "arxiv_categories": ["cs.AI"],
                "arxiv_relevance_terms": ["retrieval"],
            },
        )()


class ApiArxivRouteTests(unittest.TestCase):
    def test_pipeline_arxiv_sync_route_uses_defaults(self) -> None:
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

                fake = _FakeContainer()
                with patch("research_rag.api.app.build_container", return_value=fake):
                    from research_rag.api.app import create_app

                    client = TestClient(create_app())
                    resp = client.post("/pipeline/arxiv/sync", json={"dry_run": True})
                    self.assertEqual(resp.status_code, 200)
                    body = resp.json()
                    self.assertTrue(body["ok"])
                    self.assertEqual(body["query"], "rag")
                    self.assertTrue(body["dry_run"])
            finally:
                os.environ.clear()
                os.environ.update(original_env)


if __name__ == "__main__":
    unittest.main()
