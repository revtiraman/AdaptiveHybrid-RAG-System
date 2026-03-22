from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from research_rag.adapters.store import SqliteVectorStore
from research_rag.domain import Chunk, DocumentRecord


class StoreTests(unittest.TestCase):
    def test_search_returns_best_match_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            database_path = Path(tmpdir) / "rag.sqlite3"
            store = SqliteVectorStore(database_path)
            store.initialize()

            document = DocumentRecord(
                document_id="paper-1",
                source_path="/tmp/paper.pdf",
                source_name="paper.pdf",
                checksum="abc123",
                page_count=2,
                chunk_count=2,
                metadata={},
                created_at="2026-03-21T00:00:00+00:00",
                updated_at="2026-03-21T00:00:00+00:00",
            )
            store.upsert_document(document)
            store.replace_chunks(
                "paper-1",
                [
                    (
                        Chunk(
                            chunk_id="c1",
                            document_id="paper-1",
                            ordinal=0,
                            page_number=1,
                            text="retrieval augmented generation improves answers",
                            token_count=5,
                            metadata={},
                        ),
                        [1.0, 0.0, 0.0],
                    ),
                    (
                        Chunk(
                            chunk_id="c2",
                            document_id="paper-1",
                            ordinal=1,
                            page_number=2,
                            text="computer vision datasets can be noisy",
                            token_count=6,
                            metadata={},
                        ),
                        [0.0, 1.0, 0.0],
                    ),
                ],
                created_at="2026-03-21T00:00:00+00:00",
            )

            results = store.search([0.9, 0.1, 0.0], top_k=2)

            self.assertEqual(len(results), 2)
            self.assertEqual(results[0].chunk.chunk_id, "c1")
            self.assertGreater(results[0].score, results[1].score)


if __name__ == "__main__":
    unittest.main()
