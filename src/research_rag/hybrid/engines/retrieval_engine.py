from __future__ import annotations

# pyright: reportMissingImports=false

import math
import re
from collections import defaultdict

from research_rag.hybrid.domain import RetrievalCandidate, SectionChunk


class HybridRetrievalEngine:
    def __init__(self, metadata_store, vector_store, embedder, reranker, rrf_k: int = 60) -> None:
        self.metadata_store = metadata_store
        self.vector_store = vector_store
        self.embedder = embedder
        self.reranker = reranker
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        top_k: int,
        paper_ids: list[str] | None = None,
        filters: dict[str, object] | None = None,
        per_section_cap: int = 3,
    ) -> list[RetrievalCandidate]:
        filters = filters or {}
        query_embedding = self.embedder.embed([query])[0]

        vector_items = self.vector_store.query(query_embedding, top_k=top_k * 3, paper_ids=paper_ids)
        claim_items = self.vector_store.query_claims(query_embedding, top_k=top_k * 3, paper_ids=paper_ids)
        vector_rank = {item["chunk_id"]: rank for rank, item in enumerate(vector_items, start=1)}
        vector_score = {
            item["chunk_id"]: 1.0 - min(max(float(item.get("distance", 1.0)), 0.0), 2.0) / 2.0
            for item in vector_items
        }

        claim_rank: dict[str, int] = {}
        claim_headline: dict[str, str] = {}
        claim_score: dict[str, float] = {}
        for rank, item in enumerate(claim_items, start=1):
            chunk_id = str(item.get("chunk_id") or "").strip()
            if not chunk_id:
                continue
            score = 1.0 - min(max(float(item.get("distance", 1.0)), 0.0), 2.0) / 2.0
            if chunk_id not in claim_rank or rank < claim_rank[chunk_id]:
                claim_rank[chunk_id] = rank
                claim_score[chunk_id] = score
                claim_headline[chunk_id] = str(item.get("claim", "")).strip()

        corpus_chunks = self.metadata_store.fetch_chunks(paper_ids=paper_ids)
        filtered_chunks = self._apply_metadata_filters(corpus_chunks, filters)

        bm25_rank, bm25_raw = self._bm25_search(query, filtered_chunks, top_k=top_k * 3)
        chunk_map = {chunk.chunk_id: chunk for chunk in filtered_chunks}

        merged: dict[str, RetrievalCandidate] = {}
        table_focused_query = self._is_table_focused_query(query)
        for chunk_id in set(vector_rank) | set(bm25_rank) | set(claim_rank):
            chunk = chunk_map.get(chunk_id)
            if chunk is None:
                continue
            v_rank = vector_rank.get(chunk_id)
            b_rank = bm25_rank.get(chunk_id)
            c_rank = claim_rank.get(chunk_id)
            rrf = 0.0
            if v_rank is not None:
                rrf += 1.0 / (self.rrf_k + v_rank)
            if b_rank is not None:
                rrf += 1.0 / (self.rrf_k + b_rank)
            if c_rank is not None:
                # Claim hits are more precise, so they receive a boost in fusion.
                rrf += 1.3 / (self.rrf_k + c_rank)
            if table_focused_query and chunk.metadata.get("content_type") == "table":
                rrf *= 1.2

            merged[chunk_id] = RetrievalCandidate(
                chunk=chunk,
                vector_rank=v_rank,
                bm25_rank=b_rank,
                vector_score=max(vector_score.get(chunk_id, 0.0), claim_score.get(chunk_id, 0.0)),
                bm25_score=bm25_raw.get(chunk_id, 0.0),
                rrf_score=rrf,
                claim_text=claim_headline.get(chunk_id),
                context_type="claim" if chunk_id in claim_headline else "chunk",
            )

        candidates = sorted(merged.values(), key=lambda item: item.rrf_score, reverse=True)
        candidates = candidates[: top_k * 2]

        rerank_input = [
            f"{c.claim_text}\n\n{c.chunk.text}" if c.claim_text else c.chunk.text
            for c in candidates
        ]
        rerank_scores = self.reranker.score(query, rerank_input)
        for candidate, score in zip(candidates, rerank_scores, strict=False):
            candidate.rerank_score = score

        candidates.sort(key=lambda item: item.rerank_score, reverse=True)
        diversified = self._enforce_diversity(candidates, top_k=top_k, per_section_cap=per_section_cap)
        return diversified

    @staticmethod
    def _is_table_focused_query(query: str) -> bool:
        lower = query.lower()
        has_number = bool(re.search(r"\d", lower))
        markers = ["table", "accuracy", "score", "compare", "greater than", "less than", "%", "rows"]
        return has_number or any(marker in lower for marker in markers)

    @staticmethod
    def _apply_metadata_filters(chunks: list[SectionChunk], filters: dict[str, object]) -> list[SectionChunk]:
        section_filter = str(filters.get("section", "")).strip().lower()
        if not section_filter:
            return chunks
        return [chunk for chunk in chunks if chunk.section.lower() == section_filter]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[a-zA-Z0-9]+", text.lower())

    def _bm25_search(self, query: str, chunks: list[SectionChunk], top_k: int) -> tuple[dict[str, int], dict[str, float]]:
        if not chunks:
            return {}, {}

        tokenized_corpus = [self._tokenize(chunk.text) for chunk in chunks]
        query_tokens = self._tokenize(query)

        try:
            from rank_bm25 import BM25Okapi

            bm25 = BM25Okapi(tokenized_corpus)
            scores = bm25.get_scores(query_tokens)
        except ModuleNotFoundError:
            query_set = set(query_tokens)
            scores = [float(len(query_set & set(tokens))) for tokens in tokenized_corpus]

        ranked = sorted(
            [(chunks[idx].chunk_id, float(score)) for idx, score in enumerate(scores)],
            key=lambda item: item[1],
            reverse=True,
        )
        ranked = [item for item in ranked if not math.isclose(item[1], 0.0)]
        ranked = ranked[:top_k]

        rank_map = {chunk_id: idx for idx, (chunk_id, _) in enumerate(ranked, start=1)}
        score_map = {chunk_id: score for chunk_id, score in ranked}
        return rank_map, score_map

    @staticmethod
    def _enforce_diversity(
        candidates: list[RetrievalCandidate],
        top_k: int,
        per_section_cap: int,
    ) -> list[RetrievalCandidate]:
        selected: list[RetrievalCandidate] = []
        section_counts: defaultdict[str, int] = defaultdict(int)

        for candidate in candidates:
            section = candidate.chunk.section
            if section_counts[section] >= per_section_cap:
                continue
            selected.append(candidate)
            section_counts[section] += 1
            if len(selected) >= top_k:
                return selected

        if len(selected) < top_k:
            seen = {item.chunk.chunk_id for item in selected}
            for candidate in candidates:
                if candidate.chunk.chunk_id in seen:
                    continue
                selected.append(candidate)
                if len(selected) >= top_k:
                    break

        return selected
