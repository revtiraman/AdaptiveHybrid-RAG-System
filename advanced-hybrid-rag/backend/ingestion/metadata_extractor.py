"""Metadata and lightweight entity extraction helpers."""

from __future__ import annotations

import re


class MetadataExtractor:
	"""Extract structured metadata and entities from plain text."""

	def extract_basic(self, text: str) -> dict[str, object]:
		doi_match = re.search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", text, flags=re.I)
		year_match = re.search(r"\b(19|20)\d{2}\b", text)
		venue_match = re.search(
			r"(?i)\b(neurips|icml|iclr|acl|emnlp|cvpr|eccv|aaai|ijcai|kdd|www|sigir)\b",
			text,
		)
		return {
			"doi": doi_match.group(0) if doi_match else None,
			"year": int(year_match.group(0)) if year_match else None,
			"venue": venue_match.group(0).upper() if venue_match else None,
		}

	def extract_entities(self, text: str) -> list[str]:
		"""Return distinct entity-like spans using simple pattern heuristics."""
		patterns = [
			r"\b[Bb][Ee][Rr][Tt][A-Za-z0-9\-]*\b",
			r"\b[Gg][Pp][Tt][- ]?\d+(?:\.\d+)?\b",
			r"\b[A-Z][A-Za-z]+(?:Net|Former|LM)\b",
			r"\b[A-Z]{2,}\b",
		]
		entities: set[str] = set()
		for pattern in patterns:
			for value in re.findall(pattern, text):
				entities.add(value.strip())
		return sorted(entities)


__all__ = ["MetadataExtractor"]
