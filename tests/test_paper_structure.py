from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from research_rag.hybrid.domain import PaperRecord, SectionChunk
from research_rag.hybrid.engines.claim_extractor import ClaimExtractor
from research_rag.hybrid.storage.sqlite_store import MetadataStore


class PaperStructureTests(unittest.TestCase):
    def test_fetch_paper_structure_aggregates_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "meta.sqlite3"
            store = MetadataStore(db)
            store.initialize()

            now = "2026-03-23T00:00:00+00:00"
            store.upsert_paper(
                PaperRecord(
                    paper_id="paper-1",
                    title="Structure Paper",
                    source_path="/tmp/x.pdf",
                    checksum="abc",
                    page_count=1,
                    chunk_count=2,
                    created_at=now,
                    updated_at=now,
                )
            )
            chunks = [
                SectionChunk("c1", "paper-1", 1, "method", 0, "We propose a retrieval method with 91.2% score.", 47, {}),
                SectionChunk("c2", "paper-1", 1, "table", 1, "[TABLE] | metric | value |", 26, {"content_type": "table"}),
            ]
            store.replace_chunks("paper-1", chunks, created_at=now)
            claims = ClaimExtractor().extract_from_chunks([chunks[0]])
            store.replace_claims("paper-1", claims, created_at=now)

            structure = store.fetch_paper_structure("paper-1")

            self.assertEqual(structure["total_chunks"], 2)
            self.assertGreaterEqual(structure["total_claims"], 1)
            self.assertEqual(structure["total_tables"], 1)
            self.assertTrue(any(item["section"] == "method" for item in structure["sections"]))


if __name__ == "__main__":
    unittest.main()
