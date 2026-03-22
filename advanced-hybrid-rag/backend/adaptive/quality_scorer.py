"""Retrieval quality scoring for adaptive control."""

from __future__ import annotations

import re

import numpy as np
from pydantic import BaseModel, Field

from ..ingestion.models import Chunk


class QualityMetrics(BaseModel):
	relevance_score: float
	diversity_score: float
	coverage_score: float
	completeness_score: float
	overall_quality: float
	issues: list[str] = Field(default_factory=list)


class RetrievalQualityScorer:
	"""Compute retrieval quality signals used by adaptive loops."""

	def score(self, query: str, query_embedding: np.ndarray, results: list[Chunk]) -> QualityMetrics:
		if not results:
			return QualityMetrics(
				relevance_score=0.0,
				diversity_score=0.0,
				coverage_score=0.0,
				completeness_score=0.0,
				overall_quality=0.0,
				issues=["no_results"],
			)

		relevance = self._relevance(query, results)
		diversity = self._diversity(results)
		coverage = self._coverage(query, results)
		completeness = self._completeness(query, results)

		overall = 0.4 * relevance + 0.25 * diversity + 0.20 * coverage + 0.15 * completeness
		issues = []
		if relevance < 0.4:
			issues.append("low_relevance")
		if diversity < 0.35:
			issues.append("low_diversity")
		if coverage < 0.45:
			issues.append("low_coverage")
		if completeness < 0.4:
			issues.append("low_completeness")

		return QualityMetrics(
			relevance_score=float(np.clip(relevance, 0.0, 1.0)),
			diversity_score=float(np.clip(diversity, 0.0, 1.0)),
			coverage_score=float(np.clip(coverage, 0.0, 1.0)),
			completeness_score=float(np.clip(completeness, 0.0, 1.0)),
			overall_quality=float(np.clip(overall, 0.0, 1.0)),
			issues=issues,
		)

	def _relevance(self, query: str, results: list[Chunk]) -> float:
		q_terms = set(self._keywords(query))
		if not q_terms:
			return 0.5
		scores = []
		for chunk in results:
			terms = set(self._keywords(chunk.text))
			denom = len(q_terms | terms) or 1
			scores.append(len(q_terms & terms) / denom)
		return float(np.mean(scores)) if scores else 0.0

	def _diversity(self, results: list[Chunk]) -> float:
		doc_ratio = len({c.metadata.doc_id for c in results}) / max(1, len(results))
		emb = [np.asarray(c.embedding, dtype=np.float32) for c in results if c.embedding]
		if len(emb) < 2:
			return doc_ratio
		dists = []
		for i in range(len(emb)):
			for j in range(i + 1, len(emb)):
				sim = _cosine(emb[i], emb[j])
				dists.append(1.0 - sim)
		mmr_component = float(np.mean(dists)) if dists else 0.0
		return 0.5 * doc_ratio + 0.5 * mmr_component

	def _coverage(self, query: str, results: list[Chunk]) -> float:
		q_terms = self._keywords(query)
		if not q_terms:
			return 0.5
		context = " ".join(c.text.lower() for c in results)
		covered = sum(1 for t in q_terms if t in context)
		entities = [t for t in q_terms if t[0].isupper()]
		ent_cov = sum(1 for e in entities if e.lower() in context) / (len(entities) or 1)
		term_cov = covered / max(1, len(q_terms))
		return 0.7 * term_cov + 0.3 * ent_cov

	def _completeness(self, query: str, results: list[Chunk]) -> float:
		subtopics = [s.strip() for s in re.split(r"\band\b|,|;|\?|\bvs\b", query, flags=re.I) if s.strip()]
		if len(subtopics) <= 1:
			return 1.0
		text = " ".join(c.text.lower() for c in results)
		hits = 0
		for topic in subtopics:
			topic_terms = self._keywords(topic)
			if any(term in text for term in topic_terms):
				hits += 1
		return hits / max(1, len(subtopics))

	def _keywords(self, text: str) -> list[str]:
		stop = {
			"the",
			"is",
			"are",
			"a",
			"an",
			"of",
			"in",
			"on",
			"to",
			"for",
			"what",
			"how",
			"why",
			"does",
			"do",
		}
		return [w for w in re.findall(r"[A-Za-z0-9_\-]+", text.lower()) if w not in stop and len(w) > 2]


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
	denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
	return float(np.dot(a, b) / denom)


__all__ = ["QualityMetrics", "RetrievalQualityScorer"]
