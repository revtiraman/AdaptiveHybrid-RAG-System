from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from research_rag.hybrid.domain import VerificationResult
from research_rag.hybrid.engines.adaptive_engine import AdaptiveCorrectiveEngine
from research_rag.hybrid.engines.document_understanding import (
    BBoxTextReconstructor,
    clean_extracted_text,
    extraction_quality_score,
)


class HybridFoundationTests(unittest.TestCase):
    def test_extraction_quality_score_prefers_readable_text(self) -> None:
        readable = "This is a readable sentence with normal spacing and mostly alphabetic characters."
        garbled = "ThsSntncHsNSpcs12345%%%%"

        self.assertGreater(extraction_quality_score(readable), extraction_quality_score(garbled))

    def test_clean_extracted_text_repairs_camel_case_and_spacing(self) -> None:
        raw = "MultiHeadAttentionusesqueries,keysandvalues"
        cleaned = clean_extracted_text(raw)

        self.assertIn("Multi Head Attentionusesqueries, keysandvalues", cleaned)

    def test_detect_columns_identifies_bimodal_distribution(self) -> None:
        reconstructor = BBoxTextReconstructor()
        page_width = 1000.0

        words = []
        for idx in range(20):
            words.append((60.0 + idx, 100.0, 120.0 + idx, 110.0, "left", 0, 0, idx))
            words.append((620.0 + idx, 100.0, 680.0 + idx, 110.0, "right", 0, 0, idx))

        self.assertEqual(reconstructor.detect_columns(page_width=page_width, words=words), 2)

    def test_adaptive_should_retry_on_low_quality(self) -> None:
        engine = AdaptiveCorrectiveEngine(base_k=10, max_k=30, max_retries=3)
        verification = VerificationResult(supported=True, confidence=0.91, unsupported_claims=[])

        self.assertTrue(engine.should_retry(verification=verification, quality=0.2, retries=0))
        self.assertFalse(engine.should_retry(verification=verification, quality=0.7, retries=3))

    def test_adaptive_verifier_flags_template_noise(self) -> None:
        engine = AdaptiveCorrectiveEngine(base_k=10, max_k=30, max_retries=3)
        answer = "Example Query 2: Multi-Hop. Confidence: High. Grounding: Verified."
        verification = engine.verify_answer(answer=answer, contexts=["clean scientific context only"])
        self.assertFalse(verification.supported)
        self.assertLess(verification.confidence, 0.5)


if __name__ == "__main__":
    unittest.main()
