from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from research_rag.hybrid.domain import RetrievalCandidate, SectionChunk
from research_rag.hybrid.engines.context_enricher import ContextEnricher


class ContextEnricherTests(unittest.TestCase):
    def test_enrich_adds_section_and_sibling_context(self) -> None:
        chunks = [
            SectionChunk("c1", "p1", 1, "method", 0, "Transformer uses self-attention.", 32, {}),
            SectionChunk("c2", "p1", 1, "method", 1, "It uses multi-head attention with 8 heads.", 43, {}),
            SectionChunk("c3", "p1", 1, "method", 2, "Each head uses reduced dimensionality.", 38, {}),
        ]
        candidate = RetrievalCandidate(
            chunk=chunks[1],
            vector_rank=1,
            bm25_rank=1,
            vector_score=0.8,
            bm25_score=0.7,
            rrf_score=0.2,
        )

        enriched = ContextEnricher().enrich([candidate], corpus_chunks=chunks, window=1)

        self.assertEqual(len(enriched), 1)
        text = enriched[0].chunk.text
        self.assertIn("[SECTION: method]", text)
        self.assertIn(">>> It uses multi-head attention with 8 heads.", text)
        self.assertIn("Transformer uses self-attention.", text)
        self.assertIn("Each head uses reduced dimensionality.", text)
        self.assertTrue(enriched[0].chunk.metadata.get("enriched"))


if __name__ == "__main__":
    unittest.main()
