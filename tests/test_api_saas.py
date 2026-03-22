from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from research_rag.domain import Chunk, DocumentRecord

try:
    from research_rag.api.app import create_app
except RuntimeError:
    create_app = None


@unittest.skipIf(create_app is None, "FastAPI app dependencies are not installed")
class ApiSaasTests(unittest.TestCase):
    def test_api_key_auth_and_tenant_scoping(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                from fastapi.testclient import TestClient  # pyright: ignore[reportMissingImports]
            except ModuleNotFoundError:
                self.skipTest("FastAPI test dependencies are not installed")

            original_env = dict(os.environ)
            try:
                os.environ["APP_ROOT_DIR"] = tmpdir
                os.environ["RAG_STORAGE_PATH"] = "rag.sqlite3"
                os.environ["RAG_DOCUMENTS_DIR"] = "documents"
                os.environ["API_KEYS"] = "team-a:key-a,team-b:key-b"
                os.environ["EMBEDDING_PROVIDER"] = "hash"
                os.environ["GENERATION_PROVIDER"] = "extractive"

                app = create_app()
                client = TestClient(app)
                self._seed_documents(app)

                unauthorized = client.get("/v1/documents")
                self.assertEqual(unauthorized.status_code, 401)

                team_a_documents = client.get("/v1/documents", headers={"x-api-key": "key-a"})
                self.assertEqual(team_a_documents.status_code, 200)
                payload = team_a_documents.json()
                self.assertEqual(len(payload["documents"]), 1)
                self.assertEqual(payload["documents"][0]["document_id"], "team-a::paper-1")

                cross_tenant = client.post(
                    "/v1/query",
                    headers={"x-api-key": "key-a"},
                    json={"question": "What does this paper discuss?", "document_id": "paper-2"},
                )
                self.assertEqual(cross_tenant.status_code, 404)

                team_a_query = client.post(
                    "/v1/query",
                    headers={"x-api-key": "key-a"},
                    json={"question": "What does this paper discuss?", "top_k": 5},
                )
                self.assertEqual(team_a_query.status_code, 200)
                result = team_a_query.json()
                self.assertTrue(result["retrieved_chunks"])
                self.assertTrue(
                    all(chunk["document_id"].startswith("team-a::") for chunk in result["retrieved_chunks"])
                )
            finally:
                os.environ.clear()
                os.environ.update(original_env)

    @staticmethod
    def _seed_documents(app) -> None:
        store = app.state.container.store

        document_a = DocumentRecord(
            document_id="team-a::paper-1",
            source_path="/tmp/paper-1.pdf",
            source_name="paper-1.pdf",
            checksum="checksum-a",
            page_count=1,
            chunk_count=1,
            metadata={"tenant_id": "team-a"},
            created_at="2026-03-22T00:00:00+00:00",
            updated_at="2026-03-22T00:00:00+00:00",
        )
        document_b = DocumentRecord(
            document_id="team-b::paper-2",
            source_path="/tmp/paper-2.pdf",
            source_name="paper-2.pdf",
            checksum="checksum-b",
            page_count=1,
            chunk_count=1,
            metadata={"tenant_id": "team-b"},
            created_at="2026-03-22T00:00:00+00:00",
            updated_at="2026-03-22T00:00:00+00:00",
        )
        store.upsert_document(document_a)
        store.upsert_document(document_b)

        vector = [1.0] * 384
        store.replace_chunks(
            "team-a::paper-1",
            [
                (
                    Chunk(
                        chunk_id="team-a::c1",
                        document_id="team-a::paper-1",
                        ordinal=0,
                        page_number=1,
                        text="This paper discusses retrieval quality improvements.",
                        token_count=7,
                        metadata={"tenant_id": "team-a"},
                    ),
                    vector,
                )
            ],
            created_at="2026-03-22T00:00:00+00:00",
        )
        store.replace_chunks(
            "team-b::paper-2",
            [
                (
                    Chunk(
                        chunk_id="team-b::c1",
                        document_id="team-b::paper-2",
                        ordinal=0,
                        page_number=1,
                        text="This is team B private content.",
                        token_count=6,
                        metadata={"tenant_id": "team-b"},
                    ),
                    vector,
                )
            ],
            created_at="2026-03-22T00:00:00+00:00",
        )


if __name__ == "__main__":
    unittest.main()
