from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from research_rag.hybrid.domain import SectionChunk
from research_rag.hybrid.engines.retrieval_engine import HybridRetrievalEngine


class _DummyEmbedder:
    def embed(self, texts: list[str]) -> list[list[float]]:
        _ = texts
        return [[0.1, 0.2, 0.3]]


class _DummyReranker:
    def score(self, query: str, passages: list[str]) -> list[float]:
        q = query.lower()
        out = []
        for p in passages:
            text = p.lower()
            out.append(1.0 if "attention" in text and "attention" in q else 0.2)
        return out


class _DummyVectorStore:
    def query(self, query_vector: list[float], top_k: int, paper_ids: list[str] | None = None):
        _ = query_vector
        _ = top_k
        _ = paper_ids
        return [
            {"chunk_id": "chunk-b", "distance": 0.1},
        ]

    def query_claims(self, query_vector: list[float], top_k: int, paper_ids: list[str] | None = None):
        _ = query_vector
        _ = top_k
        _ = paper_ids
        return [
            {
                "claim_id": "claim-1",
                "chunk_id": "chunk-a",
                "claim": "The model uses multi-head attention with 8 heads.",
                "distance": 0.05,
            }
        ]


class _DummyMetadataStore:
    def fetch_chunks(self, paper_ids: list[str] | None = None):
        _ = paper_ids
        return [
            SectionChunk(
                chunk_id="chunk-a",
                paper_id="paper-1",
                page_number=2,
                section="method",
                ordinal=0,
                text="The architecture includes encoder and decoder blocks.",
                char_count=58,
                metadata={},
            ),
            SectionChunk(
                chunk_id="chunk-b",
                paper_id="paper-1",
                page_number=3,
                section="results",
                ordinal=1,
                text="Results are summarized with BLEU score.",
                char_count=40,
                metadata={},
            ),
        ]


class ClaimRetrieverIntegrationTests(unittest.TestCase):
    def test_claim_hits_are_merged_into_retrieval_candidates(self) -> None:
        engine = HybridRetrievalEngine(
            metadata_store=_DummyMetadataStore(),
            vector_store=_DummyVectorStore(),
            embedder=_DummyEmbedder(),
            reranker=_DummyReranker(),
            rrf_k=60,
        )

        results = engine.retrieve(query="how many attention heads", top_k=2)

        self.assertTrue(any(item.context_type == "claim" for item in results))
        claim_items = [item for item in results if item.context_type == "claim"]
        self.assertTrue(claim_items)
        self.assertIn("multi-head attention", (claim_items[0].claim_text or "").lower())


if __name__ == "__main__":
    unittest.main()
