"""Query decomposition helpers."""

from __future__ import annotations

import re


class QueryDecomposer:
	"""Break complex user queries into smaller sub-questions."""

	def decompose(self, query: str) -> list[str]:
		parts = [p.strip() for p in re.split(r"\band\b|;|,", query, flags=re.I) if p.strip()]
		if len(parts) <= 1:
			return [query.strip()]
		return [p if p.endswith("?") else f"{p}?" for p in parts[:5]]


__all__ = ["QueryDecomposer"]
