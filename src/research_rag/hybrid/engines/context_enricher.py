from __future__ import annotations

from dataclasses import replace

from research_rag.hybrid.domain import RetrievalCandidate, SectionChunk


class ContextEnricher:
    """Augment retrieved chunks with section-aware sibling context."""

    def enrich(
        self,
        candidates: list[RetrievalCandidate],
        corpus_chunks: list[SectionChunk],
        window: int = 1,
    ) -> list[RetrievalCandidate]:
        if not candidates:
            return []

        by_key: dict[tuple[str, str], list[SectionChunk]] = {}
        for chunk in corpus_chunks:
            key = (chunk.paper_id, chunk.section)
            by_key.setdefault(key, []).append(chunk)

        for key in by_key:
            by_key[key].sort(key=lambda c: c.ordinal)

        enriched: list[RetrievalCandidate] = []
        for candidate in candidates:
            key = (candidate.chunk.paper_id, candidate.chunk.section)
            siblings = by_key.get(key, [])
            idx = self._find_index(siblings, candidate.chunk.chunk_id)
            if idx is None:
                enriched.append(candidate)
                continue

            prev_chunks = siblings[max(0, idx - window) : idx]
            next_chunks = siblings[idx + 1 : idx + 1 + window]
            prev_text = " ".join(c.text for c in prev_chunks).strip()
            next_text = " ".join(c.text for c in next_chunks).strip()
            section_summary = siblings[0].text.split(".")[0].strip() if siblings else ""

            full = self._assemble(
                section=candidate.chunk.section,
                preceding=prev_text,
                main=candidate.chunk.text,
                following=next_text,
            )

            metadata = dict(candidate.chunk.metadata)
            metadata.update(
                {
                    "section_summary": section_summary,
                    "preceding_context": prev_text[:220],
                    "following_context": next_text[:220],
                    "enriched": True,
                    "main_chunk_text": candidate.chunk.text,
                }
            )

            enriched_chunk = replace(candidate.chunk, text=full, char_count=len(full), metadata=metadata)
            enriched.append(
                RetrievalCandidate(
                    chunk=enriched_chunk,
                    vector_rank=candidate.vector_rank,
                    bm25_rank=candidate.bm25_rank,
                    vector_score=candidate.vector_score,
                    bm25_score=candidate.bm25_score,
                    rrf_score=candidate.rrf_score,
                    rerank_score=candidate.rerank_score,
                    claim_text=candidate.claim_text,
                    context_type=candidate.context_type,
                )
            )

        return enriched

    @staticmethod
    def _find_index(chunks: list[SectionChunk], chunk_id: str) -> int | None:
        for idx, chunk in enumerate(chunks):
            if chunk.chunk_id == chunk_id:
                return idx
        return None

    @staticmethod
    def _assemble(section: str, preceding: str, main: str, following: str) -> str:
        parts = [f"[SECTION: {section}]"]
        if preceding:
            parts.append(preceding)
        parts.append(f">>> {main}")
        if following:
            parts.append(following)
        return "\n".join(parts).strip()
