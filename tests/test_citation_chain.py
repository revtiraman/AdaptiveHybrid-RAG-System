from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from research_rag.hybrid.domain import RetrievalCandidate, SectionChunk
from research_rag.hybrid.engines.citation_chain_retriever import CitationChainRetriever


class _Paper:
    def __init__(self, paper_id: str, title: str) -> None:
        self.paper_id = paper_id
        self.title = title


class _MetadataStore:
    def list_papers(self):
        return [
            _Paper("p-main", "Primary Document"),
            _Paper("p-attn", "Attention Is All You Need"),
            _Paper("p-other", "Unrelated Biology Paper"),
        ]

    def fetch_chunks(self, paper_ids=None):
        if paper_ids == ["p-attn"]:
            return [
                SectionChunk("c-attn-1", "p-attn", 4, "method", 0, "The model uses 8 attention heads.", 34, {}),
                SectionChunk("c-attn-2", "p-attn", 5, "results", 1, "Multi-head attention improves learning.", 39, {}),
            ]
        return []


class CitationChainTests(unittest.TestCase):
    def test_retrieves_chunks_from_cited_in_corpus_paper(self) -> None:
        primary = [
            RetrievalCandidate(
                chunk=SectionChunk(
                    "c-main",
                    "p-main",
                    1,
                    "introduction",
                    0,
                    "We build on (Vaswani et al. 2017) to improve sequence modeling.",
                    66,
                    {},
                ),
                vector_rank=1,
                bm25_rank=1,
                vector_score=0.8,
                bm25_score=0.7,
                rrf_score=0.2,
            )
        ]

        retriever = CitationChainRetriever(_MetadataStore())
        extras = retriever.retrieve_with_citations(
            query="how many attention heads",
            primary_candidates=primary,
            max_papers=2,
            top_chunks_per_paper=2,
        )

        self.assertGreaterEqual(len(extras), 1)
        self.assertTrue(any(item.chunk.paper_id == "p-attn" for item in extras))
        self.assertTrue(all(item.chunk.metadata.get("citation_source") is True for item in extras))


if __name__ == "__main__":
    unittest.main()
