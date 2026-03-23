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
    def evaluate(self, dataset_path: str, limit: int | None = None):
        return {"cases": 1, "dataset_path": dataset_path, "limit": limit}

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


class ApiEvalRouteTests(unittest.TestCase):
    def test_eval_run_route(self) -> None:
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
                    resp = client.post("/eval/run", json={"dataset_path": "/tmp/eval.json", "limit": 5})
                    self.assertEqual(resp.status_code, 200)
                    body = resp.json()
                    self.assertEqual(body["cases"], 1)
                    self.assertEqual(body["limit"], 5)
            finally:
                os.environ.clear()
                os.environ.update(original_env)


if __name__ == "__main__":
    unittest.main()
