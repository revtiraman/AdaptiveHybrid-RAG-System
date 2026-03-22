from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from research_rag.adapters.embeddings import HashingEmbeddingProvider
from research_rag.adapters.generator import ExtractiveAnswerGenerator
from research_rag.adapters.store import SqliteVectorStore
from research_rag.domain import Chunk, DocumentRecord
from research_rag.services.query import RagQueryService


class QueryServiceTests(unittest.TestCase):
    def test_query_returns_cited_answer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            database_path = Path(tmpdir) / "rag.sqlite3"
            store = SqliteVectorStore(database_path)
            store.initialize()

            document = DocumentRecord(
                document_id="paper-1",
                source_path="/tmp/paper.pdf",
                source_name="paper.pdf",
                checksum="abc123",
                page_count=1,
                chunk_count=1,
                metadata={},
                created_at="2026-03-21T00:00:00+00:00",
                updated_at="2026-03-21T00:00:00+00:00",
            )
            store.upsert_document(document)

            provider = HashingEmbeddingProvider(dimension=128)
            chunk = Chunk(
                chunk_id="chunk-1",
                document_id="paper-1",
                ordinal=0,
                page_number=1,
                text=(
                    "The paper evaluates retrieval augmented generation on long-form question answering "
                    "and reports better groundedness than the baseline model."
                ),
                token_count=19,
                metadata={},
            )
            store.replace_chunks(
                "paper-1",
                [(chunk, provider.embed_texts([chunk.text])[0])],
                created_at="2026-03-21T00:00:00+00:00",
            )

            service = RagQueryService(
                default_top_k=3,
                embedding_provider=provider,
                store=store,
                generator=ExtractiveAnswerGenerator(),
            )
            response = service.query("What does the paper report about groundedness?")

            self.assertIn("groundedness", response.answer.lower())
            self.assertTrue(response.citations)
            self.assertEqual(response.citations[0]["page_number"], 1)


if __name__ == "__main__":
    unittest.main()
