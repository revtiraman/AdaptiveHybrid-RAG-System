from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from research_rag.hybrid.engines.adaptive_engine import AdaptiveCorrectiveEngine


class SelfVerifierExpansionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = AdaptiveCorrectiveEngine(base_k=10, max_k=30, max_retries=3)

    def test_numeric_grounding_flags_missing_number(self) -> None:
        answer = "The model achieved 99.9 accuracy on benchmark X."
        contexts = ["The model achieved 94.2 accuracy on benchmark X."]
        result = self.engine.verify_answer(answer=answer, contexts=contexts)

        self.assertFalse(result.supported)
        self.assertTrue(any(issue["type"] == "numeric" for issue in result.issues))
        self.assertLess(result.stage_scores.get("numeric", 1.0), 1.0)

    def test_entity_grounding_flags_hallucinated_entity(self) -> None:
        answer = "HyperNovaEncoder significantly improves retrieval quality."
        contexts = ["The baseline encoder improves retrieval quality in ablation studies."]
        result = self.engine.verify_answer(answer=answer, contexts=contexts)

        self.assertTrue(any(issue["type"] == "entity" for issue in result.issues))
        self.assertLess(result.stage_scores.get("entity", 1.0), 1.0)

    def test_citation_sanity_flags_unknown_reference(self) -> None:
        answer = "This behavior is validated [missing_chunk_42]."
        contexts = ["Known supporting evidence from chunk_12 and chunk_19."]
        result = self.engine.verify_answer(answer=answer, contexts=contexts)

        self.assertTrue(any(issue["type"] == "citation" for issue in result.issues))
        self.assertLess(result.stage_scores.get("citation", 1.0), 1.0)

    def test_completeness_flags_short_answer(self) -> None:
        answer = "Works well."
        contexts = ["The method works well under controlled conditions."]
        result = self.engine.verify_answer(answer=answer, contexts=contexts)

        self.assertTrue(any(issue["type"] == "completeness" for issue in result.issues))
        self.assertLess(result.stage_scores.get("completeness", 1.0), 1.0)


if __name__ == "__main__":
    unittest.main()
