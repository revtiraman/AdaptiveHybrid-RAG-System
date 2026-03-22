"""Citation attachment and bibliography generation."""

from __future__ import annotations

import re

from ..ingestion.models import Chunk
from .structured_output import AnnotatedAnswer, Citation


class CitationGenerator:
	"""Attach best-supporting citations to answer sentences."""

	def __init__(self, citation_threshold: float = 0.65) -> None:
		self.citation_threshold = citation_threshold

	def generate_citations(self, answer: str, retrieved_chunks: list[Chunk], style: str = "inline") -> AnnotatedAnswer:
		sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer) if s.strip()]
		bibliography: list[Citation] = []
		uncited: list[str] = []
		out_sentences: list[str] = []

		for sentence in sentences:
			best = self._best_chunk(sentence, retrieved_chunks)
			if best is None:
				uncited.append(sentence)
				out_sentences.append(sentence)
				continue
			chunk, score = best
			if score < self.citation_threshold:
				uncited.append(sentence)
				out_sentences.append(sentence)
				continue

			citation = Citation(
				doc_id=chunk.metadata.doc_id,
				doc_title=chunk.metadata.source_file,
				authors=[],
				year=None,
				venue=None,
				doi=None,
				chunk_id=chunk.metadata.chunk_id,
				page_numbers=list(range(chunk.metadata.page_start, chunk.metadata.page_end + 1)),
				relevant_excerpt=chunk.text[:200],
				support_score=score,
			)
			bibliography.append(citation)
			marker = self._format_marker(citation, style)
			out_sentences.append(f"{sentence} {marker}")

		return AnnotatedAnswer(
			text_with_inline_cites=" ".join(out_sentences),
			bibliography=bibliography,
			uncited_sentences=uncited,
		)

	def _best_chunk(self, sentence: str, chunks: list[Chunk]) -> tuple[Chunk, float] | None:
		if not chunks:
			return None
		scores = []
		s_terms = set(sentence.lower().split())
		for chunk in chunks:
			c_terms = set(chunk.text.lower().split())
			denom = len(s_terms | c_terms) or 1
			score = len(s_terms & c_terms) / denom
			scores.append((chunk, float(score)))
		scores.sort(key=lambda x: x[1], reverse=True)
		return scores[0]

	def _format_marker(self, citation: Citation, style: str) -> str:
		if style == "apa":
			return f"({citation.doc_title}, p.{citation.page_numbers[0] if citation.page_numbers else 1})"
		if style == "ieee":
			return f"[{citation.chunk_id}]"
		if style == "mla":
			return f"({citation.doc_title} {citation.page_numbers[0] if citation.page_numbers else 1})"
		return f"[{citation.chunk_id}]"


__all__ = ["CitationGenerator"]
