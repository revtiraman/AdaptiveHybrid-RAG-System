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


class DebugChunkSampleTests(unittest.TestCase):
    def test_fetch_chunk_samples_returns_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "meta.sqlite3"
            store = MetadataStore(db)
            store.initialize()

            now = "2026-03-22T00:00:00+00:00"
            store.upsert_paper(
                PaperRecord(
                    paper_id="paper-1",
                    title="Debug Paper",
                    source_path="/tmp/x.pdf",
                    checksum="abc",
                    page_count=1,
                    chunk_count=1,
                    created_at=now,
                    updated_at=now,
                )
            )
            chunk = SectionChunk(
                chunk_id="chunk-1",
                paper_id="paper-1",
                page_number=1,
                section="results",
                ordinal=0,
                text="Our model reaches 92.1% accuracy and outperforms baseline by 3.0%.",
                char_count=69,
                metadata={},
            )
            store.replace_chunks("paper-1", [chunk], created_at=now)
            claims = ClaimExtractor().extract_from_chunks([chunk])
            store.replace_claims("paper-1", claims, created_at=now)

            samples = store.fetch_chunk_samples("paper-1", limit=3)

            self.assertEqual(len(samples), 1)
            self.assertEqual(samples[0]["chunk_id"], "chunk-1")
            self.assertGreaterEqual(int(samples[0]["claim_count"]), 1)
            self.assertFalse(bool(samples[0]["looks_like_noise"]))


if __name__ == "__main__":
    unittest.main()
