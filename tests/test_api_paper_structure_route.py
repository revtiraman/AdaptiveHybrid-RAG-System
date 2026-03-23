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
        return _FakePaper("Demo") if paper_id == "paper-1" else None

    def fetch_paper_structure(self, paper_id: str):
        _ = paper_id
        return {
            "paper_id": "paper-1",
            "section_count": 2,
            "total_chunks": 10,
            "total_claims": 14,
            "total_tables": 1,
            "reference_chunk_count": 2,
            "noisy_chunk_count": 0,
            "sections": [
                {"section": "method", "chunk_count": 4, "claim_count": 8, "table_count": 0},
                {"section": "results", "chunk_count": 6, "claim_count": 6, "table_count": 1},
            ],
        }


class _FakeSystem:
    def __init__(self) -> None:
        self.metadata_store = _FakeMetadataStore()

    def stats(self):
        class _S:
            papers = 1
            chunks = 10
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


class ApiPaperStructureRouteTests(unittest.TestCase):
    def test_debug_paper_structure_route(self) -> None:
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
                    resp = client.post("/debug/paper-structure", json={"paper_id": "paper-1"})
                    self.assertEqual(resp.status_code, 200)
                    body = resp.json()
                    self.assertEqual(body["paper_id"], "paper-1")
                    self.assertEqual(body["title"], "Demo")
                    self.assertEqual(body["total_tables"], 1)
            finally:
                os.environ.clear()
                os.environ.update(original_env)


if __name__ == "__main__":
    unittest.main()
