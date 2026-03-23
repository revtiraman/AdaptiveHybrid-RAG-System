from __future__ import annotations

from datetime import datetime, timezone
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from research_rag.hybrid.engines.arxiv_pipeline import ArxivAutoPipeline


_SAMPLE_FEED = b"""<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns='http://www.w3.org/2005/Atom'>
  <entry>
    <id>http://arxiv.org/abs/2501.12345v2</id>
    <updated>2026-03-20T11:00:00Z</updated>
    <title>Adaptive Retrieval for Scientific QA</title>
    <summary>This work improves retrieval augmented generation for scientific QA.</summary>
    <link rel='alternate' type='text/html' href='http://arxiv.org/abs/2501.12345v2'/>
    <link title='pdf' rel='related' type='application/pdf' href='http://arxiv.org/pdf/2501.12345v2'/>
    <category term='cs.AI'/>
  </entry>
</feed>
"""


class _DummyMetadataStore:
    def get_paper(self, paper_id: str):
        _ = paper_id
        return None


class _DummySystem:
    def __init__(self) -> None:
        self.metadata_store = _DummyMetadataStore()
        self.ingested_calls = 0

    def ingest_pdf(self, pdf_path: str, title: str | None = None, paper_id: str | None = None):
        self.ingested_calls += 1
        _ = (pdf_path, title, paper_id)
        return {"chunk_count": 12}


class _Response:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def read(self):
        return self.payload


class ArxivPipelineTests(unittest.TestCase):
    def test_parse_feed_extracts_arxiv_id_without_version(self) -> None:
        entries = ArxivAutoPipeline._parse_feed(_SAMPLE_FEED)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].arxiv_id, "2501.12345")
        self.assertEqual(entries[0].categories, ["cs.AI"])

    def test_filter_by_category_term_and_date(self) -> None:
        entries = ArxivAutoPipeline._parse_feed(_SAMPLE_FEED)
        pipeline = ArxivAutoPipeline(system=_DummySystem(), documents_dir=Path("/tmp"))
        filtered = pipeline.filter_entries(
            entries,
            query="retrieval augmented generation",
            days_back=365,
            categories=["cs.AI"],
            relevance_terms=["retrieval", "generation"],
        )
        self.assertEqual(len(filtered), 1)

        filtered_out = pipeline.filter_entries(
            entries,
            query="retrieval augmented generation",
            days_back=365,
            categories=["cs.CL"],
            relevance_terms=["retrieval"],
        )
        self.assertEqual(filtered_out, [])

    def test_run_dry_run_does_not_ingest(self) -> None:
        system = _DummySystem()
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = ArxivAutoPipeline(system=system, documents_dir=Path(tmpdir))

            with patch("research_rag.hybrid.engines.arxiv_pipeline.urlopen", return_value=_Response(_SAMPLE_FEED)):
                summary = pipeline.run(
                    query="retrieval augmented generation",
                    max_results=3,
                    days_back=365,
                    categories=["cs.AI"],
                    relevance_terms=["retrieval"],
                    dry_run=True,
                )

        self.assertEqual(system.ingested_calls, 0)
        self.assertEqual(summary["fetched"], 1)
        self.assertEqual(summary["matched"], 1)
        self.assertEqual(len(summary["skipped"]), 1)
        self.assertEqual(summary["skipped"][0]["reason"], "dry-run")


if __name__ == "__main__":
    unittest.main()
