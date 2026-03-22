"""Intent and complexity analysis for incoming queries."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field


class QueryAnalysis(BaseModel):
	query_type: Literal[
		"simple_fact",
		"comparative",
		"multi_hop",
		"causal",
		"procedural",
		"temporal",
		"quantitative",
		"survey",
	]
	complexity: Literal["low", "medium", "high"]
	entities: list[str] = Field(default_factory=list)
	requires_synthesis: bool
	is_ambiguous: bool
	suggested_mode: str
	estimated_sources_needed: int


class QueryAnalyzer:
	"""Heuristic query analyzer to guide downstream reasoning mode."""

	def analyze(self, query: str) -> QueryAnalysis:
		q = query.lower()
		entities = re.findall(r"\b[A-Z][A-Za-z0-9\-]+\b", query)

		query_type: QueryAnalysis.__annotations__["query_type"] = "simple_fact"
		if any(k in q for k in ["compare", "vs", "difference between"]):
			query_type = "comparative"
		elif any(k in q for k in ["why", "cause", "because"]):
			query_type = "causal"
		elif any(k in q for k in ["how to", "steps to"]):
			query_type = "procedural"
		elif any(k in q for k in ["timeline", "over time", "evolution"]):
			query_type = "temporal"
		elif any(k in q for k in ["accuracy", "f1", "precision", "recall", "metric"]):
			query_type = "quantitative"
		elif any(k in q for k in ["survey", "overview", "landscape"]):
			query_type = "survey"
		elif len(entities) >= 2 or any(k in q for k in ["and", "relation", "impact of"]):
			query_type = "multi_hop"

		complexity = "low"
		if len(query.split()) > 12 or query_type in {"multi_hop", "survey", "comparative"}:
			complexity = "medium"
		if len(query.split()) > 22 or query_type in {"survey", "multi_hop"}:
			complexity = "high"

		ambiguous = len(query.strip()) < 8 or any(k in q for k in ["this", "that", "it"]) and not entities
		requires_synthesis = query_type in {"multi_hop", "survey", "comparative", "temporal"}
		mode = "basic"
		if query_type == "multi_hop":
			mode = "multihop"
		elif query_type == "comparative":
			mode = "comparison"

		sources = 2
		if complexity == "medium":
			sources = 4
		if complexity == "high":
			sources = 6

		return QueryAnalysis(
			query_type=query_type,
			complexity=complexity,
			entities=entities,
			requires_synthesis=requires_synthesis,
			is_ambiguous=ambiguous,
			suggested_mode=mode,
			estimated_sources_needed=sources,
		)


__all__ = ["QueryAnalysis", "QueryAnalyzer"]
