from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from research_rag.chunking import chunk_pages
from research_rag.domain import SourcePage


class ChunkingTests(unittest.TestCase):
    def test_chunk_pages_preserves_page_number_and_overlap(self) -> None:
        pages = [
            SourcePage(
                page_number=1,
                text=(
                    "Large language models are useful for research assistants. "
                    "They can summarize evidence. They can also answer grounded questions. "
                    "Retrieval improves factual accuracy when the system cites the source."
                ),
            )
        ]

        chunks = chunk_pages(document_id="paper-1", pages=pages, chunk_size=10, chunk_overlap=3)

        self.assertGreaterEqual(len(chunks), 2)
        self.assertTrue(all(chunk.page_number == 1 for chunk in chunks))
        self.assertEqual(chunks[0].document_id, "paper-1")
        self.assertGreater(chunks[0].token_count, 0)
        overlap_words = set(chunks[0].text.split()[-3:])
        self.assertTrue(overlap_words.intersection(chunks[1].text.split()))


if __name__ == "__main__":
    unittest.main()
