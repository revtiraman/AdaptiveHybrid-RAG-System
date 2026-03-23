from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from research_rag.hybrid.domain import SectionChunk
from research_rag.hybrid.engines.claim_extractor import ClaimExtractor
from research_rag.hybrid.storage.sqlite_store import MetadataStore


class ClaimExtractionTests(unittest.TestCase):
    def test_claim_extractor_finds_result_and_entities(self) -> None:
        chunk = SectionChunk(
            chunk_id="chunk-1",
            paper_id="paper-1",
            page_number=4,
            section="results",
            ordinal=0,
            text=(
                "Our model achieves 91.2% accuracy on CIFAR10 and outperforms the baseline by 3.4%. "
                "We plan future work on multilingual transfer."
            ),
            char_count=130,
            metadata={},
        )

        claims = ClaimExtractor().extract_from_chunks([chunk])

        self.assertGreaterEqual(len(claims), 1)
        self.assertTrue(any(c.claim_type in {"result", "comparison"} for c in claims))
        self.assertTrue(any("91.2" in " ".join(c.entities) for c in claims))

    def test_metadata_store_persists_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "meta.sqlite3"
            store = MetadataStore(db)
            store.initialize()

            # Seed required paper/chunk rows before claims because of FK constraints.
            from research_rag.hybrid.domain import PaperRecord

            now = "2026-03-22T00:00:00+00:00"
            store.upsert_paper(
                PaperRecord(
                    paper_id="paper-1",
                    title="Test Paper",
                    source_path="/tmp/x.pdf",
                    checksum="abc",
                    page_count=1,
                    chunk_count=1,
                    created_at=now,
                    updated_at=now,
                )
            )
            store.replace_chunks(
                "paper-1",
                [
                    SectionChunk(
                        chunk_id="chunk-1",
                        paper_id="paper-1",
                        page_number=1,
                        section="results",
                        ordinal=0,
                        text="The method reaches 88.0% accuracy on DatasetX.",
                        char_count=46,
                        metadata={},
                    )
                ],
                created_at=now,
            )

            claims = ClaimExtractor().extract_from_chunks(store.fetch_chunks(["paper-1"]))
            store.replace_claims("paper-1", claims, created_at=now)

            self.assertEqual(store.count_claims("paper-1"), len(claims))
            self.assertGreater(store.count_claims("paper-1"), 0)


if __name__ == "__main__":
    unittest.main()
