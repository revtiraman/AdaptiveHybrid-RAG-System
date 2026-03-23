from __future__ import annotations

from hashlib import sha1
import re

from research_rag.hybrid.domain import ClaimRecord, SectionChunk


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_ENTITY_PATTERN = re.compile(r"\b([A-Z][A-Za-z0-9_\-]{2,}|\d+(?:\.\d+)?%?)\b")


class ClaimExtractor:
    """Extract lightweight atomic factual claims from chunk text."""

    def extract_from_chunks(self, chunks: list[SectionChunk]) -> list[ClaimRecord]:
        claims: list[ClaimRecord] = []

        for chunk in chunks:
            sentences = [s.strip() for s in _SENTENCE_SPLIT.split(chunk.text) if s.strip()]
            for sent_idx, sentence in enumerate(sentences):
                if not self._is_claim_candidate(sentence):
                    continue
                claim_type = self._infer_claim_type(sentence, chunk.section)
                entities = sorted(set(_ENTITY_PATTERN.findall(sentence)))[:10]
                confidence = self._confidence(sentence, claim_type)
                claim_id = sha1(f"{chunk.chunk_id}:{sent_idx}:{sentence}".encode("utf-8")).hexdigest()

                claims.append(
                    ClaimRecord(
                        claim_id=claim_id,
                        paper_id=chunk.paper_id,
                        chunk_id=chunk.chunk_id,
                        claim=sentence,
                        claim_type=claim_type,
                        section=chunk.section,
                        page_number=chunk.page_number,
                        entities=entities,
                        confidence=confidence,
                        metadata={"source": "heuristic_claim_extractor"},
                    )
                )

        return claims

    @staticmethod
    def _is_claim_candidate(sentence: str) -> bool:
        lower = sentence.lower()
        if len(sentence) < 35:
            return False
        if len(sentence.split()) < 7:
            return False
        if any(token in lower for token in ["future work", "we plan", "might", "could", "todo"]):
            return False
        if re.search(r"\b(table|figure|appendix)\b\s*\d+", lower):
            return False
        return True

    @staticmethod
    def _infer_claim_type(sentence: str, section: str) -> str:
        lower = sentence.lower()
        section_lower = (section or "").lower()

        if any(key in lower for key in ["outperform", "better than", "compared to", "versus"]):
            return "comparison"
        if any(key in lower for key in ["define", "is called", "refers to", "means"]):
            return "definition"
        if any(key in lower for key in ["limitation", "fails", "weakness", "not robust", "degrade"]):
            return "limitation"
        if "method" in section_lower or any(key in lower for key in ["we propose", "we introduce", "our approach"]):
            return "method"
        return "result"

    @staticmethod
    def _confidence(sentence: str, claim_type: str) -> float:
        score = 0.55
        if re.search(r"\b\d+(?:\.\d+)?%?\b", sentence):
            score += 0.1
        if claim_type in {"result", "comparison"}:
            score += 0.1
        if len(sentence.split()) >= 14:
            score += 0.1
        return round(min(0.95, score), 3)
