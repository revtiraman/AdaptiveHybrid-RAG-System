"""Self-verification checks for answer grounding and quality."""

from __future__ import annotations

import re

from ..ingestion.models import Chunk
from .structured_output import VerificationIssue, VerificationResult


class SelfVerifier:
	"""Validate grounding, citations, and internal consistency."""

	_ENTITY_STOPWORDS = {
		"the",
		"this",
		"that",
		"these",
		"those",
		"we",
		"it",
		"they",
		"our",
		"their",
		"a",
		"an",
		"in",
		"on",
		"for",
		"and",
		"or",
		"but",
		"however",
		"therefore",
	}

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

		entity_issues = self._entity_hallucination_check(query, answer, chunk_text)
		issues.extend(entity_issues)

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

		claims = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer) if s.strip()]
		affirmed: set[str] = set()
		negated: set[str] = set()
		for claim in claims:
			terms = {t for t in re.findall(r"\b[a-z]{4,}\b", claim.lower())}
			if not terms:
				continue
			if re.search(r"\b(no|not|never|cannot|can't|without)\b", claim.lower()):
				negated.update(terms)
			else:
				affirmed.update(terms)

		contradicted = sorted((affirmed & negated) - {"that", "with", "from", "this"})
		if contradicted:
			issues.append(
				VerificationIssue(
					issue_type="consistency",
					detail=f"Potential contradiction around terms: {', '.join(contradicted[:5])}",
					severity="high",
				)
			)
		return issues

	def _entity_hallucination_check(self, query: str, answer: str, context: str) -> list[VerificationIssue]:
		issues: list[VerificationIssue] = []
		query_entities = self._extract_entities(query)
		answer_entities = self._extract_entities(answer)
		context_entities = self._extract_entities(context)

		unknown = sorted(answer_entities - query_entities - context_entities)
		for entity in unknown[:3]:
			issues.append(
				VerificationIssue(
					issue_type="hallucination",
					detail=f"Entity not supported by query/context: {entity}",
					severity="high",
				)
			)
		return issues

	def _extract_entities(self, text: str) -> set[str]:
		candidates = set(re.findall(r"\b[A-Z][A-Za-z0-9_-]{2,}\b", text))
		return {
			token
			for token in candidates
			if token.lower() not in self._ENTITY_STOPWORDS and not token.isdigit()
		}


__all__ = ["SelfVerifier"]
