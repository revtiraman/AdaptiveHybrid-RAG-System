from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from research_rag.hybrid.engines.eval_harness import EvaluationHarness


class _FakeResult:
    def __init__(self, answer: str, retrieval_quality: float, supported: bool) -> None:
        self.answer = answer
        self.retrieval_quality = retrieval_quality
        self.retries = 0
        self.latency_ms = 12
        self.diagnostic = {"verification": {"supported": supported}}


class _FakeSystem:
    def query(self, question: str, paper_ids=None):
        _ = (question, paper_ids)
        return _FakeResult(
            answer="This paper uses retrieval augmented generation with citation grounding.",
            retrieval_quality=0.82,
            supported=True,
        )


class EvalHarnessTests(unittest.TestCase):
    def test_run_scores_keyword_recall(self) -> None:
        data = [
            {
                "question": "What method is used?",
                "expected_keywords": ["retrieval", "generation", "citation"],
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "eval.json"
            p.write_text(json.dumps(data), encoding="utf-8")

            harness = EvaluationHarness(system=_FakeSystem())
            result = harness.run(dataset_path=str(p))

        self.assertEqual(result["cases"], 1)
        self.assertGreaterEqual(result["avg_keyword_recall"], 0.66)
        self.assertEqual(result["supported_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
