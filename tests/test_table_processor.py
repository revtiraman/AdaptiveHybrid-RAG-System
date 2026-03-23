from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from research_rag.hybrid.engines.table_processor import TableProcessor


class TableProcessorTests(unittest.TestCase):
    def test_markdown_and_nl_rendering(self) -> None:
        rows = [
            ["Model", "Accuracy", "Params"],
            ["Base", "89.1", "12M"],
            ["Large", "91.4", "48M"],
        ]
        markdown = TableProcessor._to_markdown(rows)
        nl = TableProcessor._to_natural_language(rows, page_number=3)

        self.assertIn("| Model | Accuracy | Params |", markdown)
        self.assertIn("Table on page 3.", nl)
        self.assertIn("Row 1:", nl)

    def test_numeric_detection(self) -> None:
        rows = [
            ["Metric", "Value"],
            ["BLEU", "28.4"],
            ["ROUGE", "41.2"],
        ]
        self.assertTrue(TableProcessor._has_numeric_data(rows))


if __name__ == "__main__":
    unittest.main()
