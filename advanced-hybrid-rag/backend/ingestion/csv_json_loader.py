"""Load structured CSV/JSON content into normalized text form."""

from __future__ import annotations

import csv
import json
from pathlib import Path


class StructuredDataLoader:
	"""Convert CSV/JSON files into text suitable for chunking."""

	def load_csv(self, source: str | Path) -> str:
		path = Path(source)
		rows: list[str] = []
		with path.open("r", encoding="utf-8") as handle:
			reader = csv.DictReader(handle)
			for idx, row in enumerate(reader, start=1):
				pairs = ", ".join(f"{k}={v}" for k, v in row.items())
				rows.append(f"Row {idx}: {pairs}")
		return "\n".join(rows)

	def load_json(self, source: str | Path | bytes) -> str:
		if isinstance(source, bytes):
			payload = json.loads(source.decode("utf-8"))
		else:
			path = Path(source)
			payload = json.loads(path.read_text(encoding="utf-8"))
		return json.dumps(payload, indent=2, ensure_ascii=True)


__all__ = ["StructuredDataLoader"]
