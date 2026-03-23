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
            return VerificationResult(
                supported=False,
                confidence=0.0,
                unsupported_claims=["empty answer"],
                issues=[{"type": "completeness", "detail": "empty answer"}],
                stage_scores={"completeness": 0.0},
            )

        if self._is_noise_answer(answer):
            return VerificationResult(
                supported=False,
                confidence=0.15,
                unsupported_claims=["detected noisy/generated template text"],
                issues=[{"type": "noise", "detail": "detected noisy/generated template text"}],
                stage_scores={"noise": 0.0},
            )

        context_text_raw = " ".join(contexts)
        context_text = context_text_raw.lower()
        claims = [segment.strip() for segment in re.split(r"[.!?]", answer) if segment.strip()]
        unsupported: list[str] = []
        issues: list[dict[str, str]] = []
        stage_scores: dict[str, float] = {}

        for claim in claims:
            claim_terms = set(re.findall(r"[a-zA-Z0-9]+", claim.lower()))
            if len(claim_terms) < 4:
                continue
            overlap = sum(1 for term in claim_terms if term in context_text)
            if overlap / max(1, len(claim_terms)) < 0.42:
                unsupported.append(claim)

        grounding_score = 1.0 if not claims else max(0.0, 1.0 - (len(unsupported) / max(1, len(claims))))
        stage_scores["grounding"] = round(grounding_score, 4)
        for claim in unsupported:
            issues.append({"type": "grounding", "detail": claim})

        numeric_score, numeric_issues = self._numeric_consistency(answer=answer, context_text=context_text)
        stage_scores["numeric"] = round(numeric_score, 4)
        issues.extend(numeric_issues)

        citation_score, citation_issues = self._citation_sanity(answer=answer, context_text=context_text)
        stage_scores["citation"] = round(citation_score, 4)
        issues.extend(citation_issues)

        entity_score, entity_issues = self._entity_grounding(answer=answer, context_text=context_text, contexts_raw=context_text_raw)
        stage_scores["entity"] = round(entity_score, 4)
        issues.extend(entity_issues)

        completeness_score, completeness_issues = self._completeness_check(answer=answer)
        stage_scores["completeness"] = round(completeness_score, 4)
        issues.extend(completeness_issues)

        issue_penalty = min(0.45, 0.07 * len(issues))
        weighted = (
            0.38 * stage_scores.get("grounding", 0.0)
            + 0.18 * stage_scores.get("numeric", 0.0)
            + 0.15 * stage_scores.get("citation", 0.0)
            + 0.14 * stage_scores.get("entity", 0.0)
            + 0.15 * stage_scores.get("completeness", 0.0)
        )
        confidence = max(0.0, min(1.0, weighted - issue_penalty))
        supported = confidence >= 0.62 and len(unsupported) == 0
        return VerificationResult(
            supported=supported,
            confidence=round(confidence, 4),
            unsupported_claims=unsupported,
            issues=issues,
            stage_scores=stage_scores,
        )

    def should_retry(self, verification: VerificationResult, quality: float, retries: int) -> bool:
        if retries >= self.max_retries:
            return False
        if not verification.supported:
            return True
        if len(verification.issues) >= 3:
            return True
        if verification.confidence < 0.75:
            return True
        return quality < self.min_quality_threshold

    @staticmethod
    def _numeric_consistency(answer: str, context_text: str) -> tuple[float, list[dict[str, str]]]:
        answer_numbers = re.findall(r"\b\d+(?:\.\d+)?\b", answer)
        if not answer_numbers:
            return 1.0, []

        issues: list[dict[str, str]] = []
        matched = 0
        for number in answer_numbers:
            if number in context_text:
                matched += 1
            else:
                issues.append({"type": "numeric", "detail": f"number not grounded: {number}"})
        score = matched / max(1, len(answer_numbers))
        return score, issues

    @staticmethod
    def _citation_sanity(answer: str, context_text: str) -> tuple[float, list[dict[str, str]]]:
        refs = re.findall(r"\[([^\]]+)\]", answer)
        if not refs:
            return 1.0, []

        issues: list[dict[str, str]] = []
        matched = 0
        for ref in refs:
            token = ref.strip().lower()
            if token and token in context_text:
                matched += 1
            else:
                issues.append({"type": "citation", "detail": f"citation token not found in context: [{ref}]"})
        score = matched / max(1, len(refs))
        return score, issues

    @staticmethod
    def _entity_grounding(answer: str, context_text: str, contexts_raw: str) -> tuple[float, list[dict[str, str]]]:
        candidates = set(re.findall(r"\b[A-Z][a-zA-Z0-9_\-]{3,}\b", answer))
        if not candidates:
            return 1.0, []

        issues: list[dict[str, str]] = []
        matched = 0
        raw_terms = {term.lower() for term in re.findall(r"[A-Za-z0-9_\-]+", contexts_raw)}
        stop = {"This", "That", "These", "Those", "The", "And", "With", "From", "Into", "When", "Where"}
        filtered = [term for term in candidates if term not in stop]
        if not filtered:
            return 1.0, []

        for term in filtered:
            lower = term.lower()
            if lower in context_text or lower in raw_terms:
                matched += 1
            else:
                issues.append({"type": "entity", "detail": f"entity not grounded: {term}"})
        score = matched / max(1, len(filtered))
        return score, issues

    @staticmethod
    def _completeness_check(answer: str) -> tuple[float, list[dict[str, str]]]:
        clean = answer.strip()
        if len(clean) < 24:
            return 0.2, [{"type": "completeness", "detail": "answer too short"}]

        sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", clean) if segment.strip()]
        if len(sentences) == 0:
            return 0.2, [{"type": "completeness", "detail": "no complete sentence detected"}]

        if len(sentences) == 1 and len(clean) < 70:
            return 0.55, [{"type": "completeness", "detail": "single-sentence answer may be incomplete"}]

        return 1.0, []

    @staticmethod
    def _is_noise_answer(answer: str) -> bool:
        lower = answer.lower()
        patterns = [
            r"example query",
            r"mode:\s*multi-hop",
            r"confidence:\s*(high|medium|low)",
            r"grounding:\s*verified",
            r"sub-questions generated",
            r"\b\d+\s*seconds\b",
        ]
        return any(re.search(pattern, lower) for pattern in patterns)
