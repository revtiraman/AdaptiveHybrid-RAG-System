from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from research_rag.hybrid.domain import RetrievalCandidate, SectionChunk
from research_rag.hybrid.engines.reasoning_engine import ReasoningEngine


class ReasoningGuardTests(unittest.TestCase):
    def test_fallback_returns_insufficient_when_context_not_aligned(self) -> None:
        engine = ReasoningEngine(llm_client=None)
        contexts = [
            RetrievalCandidate(
                chunk=SectionChunk(
                    chunk_id="c1",
                    paper_id="p1",
                    page_number=1,
                    section="results",
                    ordinal=0,
                    text="Example Query 2: Multi-Hop. Confidence: High. Grounding: Verified.",
                    char_count=65,
                    metadata={},
                ),
                vector_rank=1,
                bm25_rank=1,
                vector_score=0.2,
                bm25_score=0.1,
                rrf_score=0.02,
            )
        ]

        answer, claims = engine.generate_answer(
            question="How many attention heads are used?",
            plan=engine.classify_query("How many attention heads are used?"),
            contexts=contexts,
        )

        self.assertIn("does not directly answer", answer.lower())
        self.assertEqual(claims, [])


if __name__ == "__main__":
    unittest.main()
