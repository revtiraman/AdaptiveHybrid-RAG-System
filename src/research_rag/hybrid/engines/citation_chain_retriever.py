from __future__ import annotations

import re

from research_rag.hybrid.domain import RetrievalCandidate, SectionChunk


_AUTHOR_YEAR = re.compile(r"\(([A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s+\d{4})\)")
_NUMBERED_REF = re.compile(r"\[(\d+)\]")


class CitationChainRetriever:
    """Retrieve additional evidence from cited papers already in corpus."""

    def __init__(self, metadata_store) -> None:
        self.metadata_store = metadata_store

    def retrieve_with_citations(
        self,
        query: str,
        primary_candidates: list[RetrievalCandidate],
        max_papers: int = 3,
        top_chunks_per_paper: int = 2,
    ) -> list[RetrievalCandidate]:
        if not primary_candidates:
            return []

        citations = self._extract_citation_strings([item.chunk.text for item in primary_candidates])
        if not citations:
            return []

        primary_paper_ids = {item.chunk.paper_id for item in primary_candidates}
        papers = self.metadata_store.list_papers()
        ranked_papers: list[tuple[float, str]] = []
        for paper in papers:
            if paper.paper_id in primary_paper_ids:
                continue
            score = self._paper_match_score(citations, query, paper.title)
            if score > 0:
                ranked_papers.append((score, paper.paper_id))

        ranked_papers.sort(key=lambda x: x[0], reverse=True)
        selected_paper_ids = [paper_id for _score, paper_id in ranked_papers[: max(0, int(max_papers))]]

        extras: list[RetrievalCandidate] = []
        for paper_id in selected_paper_ids:
            chunks = self.metadata_store.fetch_chunks([paper_id])
            scored = self._rank_chunks_by_query_overlap(query, chunks)
            for overlap_score, chunk in scored[: max(1, int(top_chunks_per_paper))]:
                md = dict(chunk.metadata)
                md["citation_source"] = True
                md["citation_depth"] = 1
                md["linked_from_query"] = query
                cited_chunk = SectionChunk(
                    chunk_id=chunk.chunk_id,
                    paper_id=chunk.paper_id,
                    page_number=chunk.page_number,
                    section=chunk.section,
                    ordinal=chunk.ordinal,
                    text=chunk.text,
                    char_count=chunk.char_count,
                    metadata=md,
                )
                extras.append(
                    RetrievalCandidate(
                        chunk=cited_chunk,
                        vector_rank=None,
                        bm25_rank=None,
                        vector_score=overlap_score,
                        bm25_score=overlap_score,
                        rrf_score=overlap_score,
                        rerank_score=overlap_score,
                        context_type="chunk",
                    )
                )

        return extras

    @staticmethod
    def _extract_citation_strings(texts: list[str]) -> list[str]:
        out: list[str] = []
        for text in texts:
            out.extend(_AUTHOR_YEAR.findall(text or ""))
            # Numbered refs are tracked as weak signals but cannot map alone.
            out.extend(_NUMBERED_REF.findall(text or ""))
        return out

    @staticmethod
    def _paper_match_score(citations: list[str], query: str, title: str) -> float:
        title_terms = set(re.findall(r"[a-zA-Z0-9]+", (title or "").lower()))
        if not title_terms:
            return 0.0

        best = 0.0
        for citation in citations:
            c_terms = set(re.findall(r"[a-zA-Z0-9]+", str(citation).lower()))
            c_terms = {t for t in c_terms if len(t) > 2 and not t.isdigit()}
            if not c_terms:
                continue
            overlap = len(c_terms & title_terms) / max(1, len(c_terms))
            best = max(best, overlap)

        query_terms = set(re.findall(r"[a-zA-Z0-9]+", query.lower()))
        query_terms = {t for t in query_terms if len(t) > 2 and not t.isdigit()}
        query_overlap = len(query_terms & title_terms) / max(1, len(query_terms)) if query_terms else 0.0

        if best > 0:
            return (0.7 * best) + (0.3 * query_overlap)
        # For author-year citations, title overlap may be absent; use query overlap as a weak fallback.
        return query_overlap if query_overlap >= 0.2 else 0.0

    @staticmethod
    def _rank_chunks_by_query_overlap(query: str, chunks: list[SectionChunk]) -> list[tuple[float, SectionChunk]]:
        q_terms = set(re.findall(r"[a-zA-Z0-9]+", query.lower()))
        q_terms = {t for t in q_terms if len(t) > 2}
        scored: list[tuple[float, SectionChunk]] = []
        for chunk in chunks:
            c_terms = set(re.findall(r"[a-zA-Z0-9]+", chunk.text.lower()))
            overlap = len(q_terms & c_terms) / max(1, len(q_terms))
            if overlap > 0:
                scored.append((overlap, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored
