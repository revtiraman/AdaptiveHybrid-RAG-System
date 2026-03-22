from __future__ import annotations

import re

from research_rag.hybrid.domain import VerificationResult


class AdaptiveCorrectiveEngine:
    def __init__(self, base_k: int, max_k: int, max_retries: int = 3) -> None:
        self.base_k = base_k
        self.max_k = max_k
        self.max_retries = max_retries
        # Keep retry policy aligned with UI quality bands so "Low" quality is corrected.
        self.min_quality_threshold = 0.45

    def retrieval_quality(self, candidates) -> float:
        if not candidates:
            return 0.0

        # Rank-based quality is more stable across different reranker score scales.
        rank_quality = 0.0
        for idx, _item in enumerate(candidates, start=1):
            rank_quality += 1.0 / idx
        rank_quality = rank_quality / max(1.0, len(candidates))

        max_rrf = max((item.rrf_score for item in candidates), default=0.0)
        rrf_norm = [item.rrf_score / max_rrf for item in candidates] if max_rrf > 0 else [0.0]
        rrf_quality = sum(rrf_norm) / max(1, len(rrf_norm))

        section_diversity = len({item.chunk.section for item in candidates}) / max(1, min(len(candidates), 5))
        normalized = min(1.0, (0.45 * rank_quality) + (0.35 * rrf_quality) + (0.20 * section_diversity))
        return round(normalized, 4)

    def choose_k(self, quality: float, retry_count: int, query_type: str) -> int:
        k = self.base_k
        if query_type == "multi_hop":
            k += 4
        if quality < 0.35:
            k += 6
        if retry_count > 0:
            k += retry_count * 3
        return min(self.max_k, max(self.base_k, k))

    def verify_answer(self, answer: str, contexts: list[str]) -> VerificationResult:
        if not answer.strip():
            return VerificationResult(supported=False, confidence=0.0, unsupported_claims=["empty answer"])

        context_text = " ".join(contexts).lower()
        claims = [segment.strip() for segment in re.split(r"[.!?]", answer) if segment.strip()]
        unsupported: list[str] = []

        for claim in claims:
            claim_terms = set(re.findall(r"[a-zA-Z0-9]+", claim.lower()))
            if len(claim_terms) < 4:
                continue
            overlap = sum(1 for term in claim_terms if term in context_text)
            if overlap / max(1, len(claim_terms)) < 0.35:
                unsupported.append(claim)

        supported = len(unsupported) == 0
        confidence = 1.0 if supported else max(0.0, 1.0 - (len(unsupported) / max(1, len(claims))))
        return VerificationResult(supported=supported, confidence=round(confidence, 4), unsupported_claims=unsupported)

    def should_retry(self, verification: VerificationResult, quality: float, retries: int) -> bool:
        if retries >= self.max_retries:
            return False
        if not verification.supported:
            return True
        return quality < self.min_quality_threshold
