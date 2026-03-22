"""Self-verification checks for answer grounding and quality."""

from __future__ import annotations

import re

from ..ingestion.models import Chunk
from .structured_output import VerificationIssue, VerificationResult


class SelfVerifier:
	"""Validate grounding, citations, and internal consistency."""

	async def verify(self, query: str, answer: str, retrieved_chunks: list[Chunk]) -> VerificationResult:
		issues: list[VerificationIssue] = []
		chunk_text = "\n".join(c.text.lower() for c in retrieved_chunks)

		claims = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer) if s.strip()]
		grounded = 0
		for claim in claims:
			if self._is_supported(claim.lower(), chunk_text):
				grounded += 1
			else:
				issues.append(VerificationIssue(issue_type="grounding", detail=f"Unsupported claim: {claim[:120]}", severity="high"))

		citation_issues = self._citation_check(answer, retrieved_chunks)
		issues.extend(citation_issues)

		consistency_issues = self._consistency_check(answer)
		issues.extend(consistency_issues)

		grounding_score = grounded / max(1, len(claims))
		citation_acc = max(0.0, 1.0 - (len(citation_issues) / max(1, len(claims))))

		action = "none"
		if grounding_score < 0.5:
			action = "re_retrieve"
		elif issues:
			action = "return_with_warning"

		return VerificationResult(
			passed=len(issues) == 0,
			issues=issues,
			corrective_action=action,
			grounding_score=grounding_score,
			citation_accuracy=citation_acc,
		)

	def _is_supported(self, claim: str, context: str) -> bool:
		terms = [w for w in re.findall(r"\w+", claim) if len(w) > 3]
		if not terms:
			return True
		hits = sum(1 for t in terms if t in context)
		return hits / len(terms) >= 0.45

	def _citation_check(self, answer: str, chunks: list[Chunk]) -> list[VerificationIssue]:
		issues: list[VerificationIssue] = []
		ids = {c.metadata.chunk_id for c in chunks}
		cited = re.findall(r"\[([^\]]+)\]", answer)
		for c in cited:
			token = c.split(",")[0].strip()
			if token and token not in ids:
				issues.append(VerificationIssue(issue_type="citation", detail=f"Unknown citation id: {token}", severity="medium"))
		return issues

	def _consistency_check(self, answer: str) -> list[VerificationIssue]:
		issues: list[VerificationIssue] = []
		if re.search(r"\b(always)\b", answer, flags=re.I) and re.search(r"\b(never)\b", answer, flags=re.I):
			issues.append(VerificationIssue(issue_type="consistency", detail="Answer contains potentially contradictory absolutes.", severity="medium"))
		return issues


__all__ = ["SelfVerifier"]
