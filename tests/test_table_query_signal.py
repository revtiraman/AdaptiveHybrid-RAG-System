from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from research_rag.hybrid.engines.retrieval_engine import HybridRetrievalEngine


class TableQuerySignalTests(unittest.TestCase):
    def test_table_query_signal_detection(self) -> None:
        self.assertTrue(HybridRetrievalEngine._is_table_focused_query("compare models with accuracy > 90%"))
        self.assertTrue(HybridRetrievalEngine._is_table_focused_query("table 3 scores"))
        self.assertFalse(HybridRetrievalEngine._is_table_focused_query("what is the main idea of the paper"))


if __name__ == "__main__":
    unittest.main()
