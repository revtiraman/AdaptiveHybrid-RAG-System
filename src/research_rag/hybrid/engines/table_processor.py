from __future__ import annotations

from hashlib import sha1
from pathlib import Path
import re

from research_rag.hybrid.domain import SectionChunk


class TableProcessor:
    """Extract table chunks with markdown and natural-language forms."""

    def extract_table_chunks(self, pdf_path: Path, paper_id: str, start_ordinal: int = 0) -> list[SectionChunk]:
        try:
            import pdfplumber
        except ModuleNotFoundError:
            return []

        chunks: list[SectionChunk] = []
        ordinal = start_ordinal

        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_idx, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables() or []
                for table_idx, table in enumerate(tables):
                    rows = self._normalize_table_rows(table)
                    if len(rows) < 2:
                        continue

                    markdown = self._to_markdown(rows)
                    nl = self._to_natural_language(rows, page_idx)
                    table_text = f"[TABLE]\n{markdown}\n\n{nl}"

                    chunk_id = sha1(f"{paper_id}:table:{page_idx}:{table_idx}:{table_text}".encode("utf-8")).hexdigest()
                    metadata = {
                        "content_type": "table",
                        "table_index": table_idx,
                        "n_rows": max(0, len(rows) - 1),
                        "n_cols": len(rows[0]) if rows else 0,
                        "has_numeric_data": self._has_numeric_data(rows),
                        "markdown": markdown,
                    }
                    chunks.append(
                        SectionChunk(
                            chunk_id=chunk_id,
                            paper_id=paper_id,
                            page_number=page_idx,
                            section="table",
                            ordinal=ordinal,
                            text=table_text,
                            char_count=len(table_text),
                            metadata=metadata,
                        )
                    )
                    ordinal += 1
        return chunks

    @staticmethod
    def _normalize_table_rows(table: list[list[str | None]]) -> list[list[str]]:
        rows: list[list[str]] = []
        width = max((len(r) for r in table), default=0)
        for row in table:
            normalized = [re.sub(r"\s+", " ", str(cell or "").strip()) for cell in row]
            if len(normalized) < width:
                normalized += [""] * (width - len(normalized))
            if any(cell for cell in normalized):
                rows.append(normalized)
        return rows

    @staticmethod
    def _to_markdown(rows: list[list[str]]) -> str:
        if not rows:
            return ""
        header = rows[0]
        body = rows[1:] if len(rows) > 1 else []
        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(["---"] * len(header)) + " |",
        ]
        for row in body:
            lines.append("| " + " | ".join(row) + " |")
        return "\n".join(lines)

    @staticmethod
    def _to_natural_language(rows: list[list[str]], page_number: int) -> str:
        if not rows:
            return ""
        headers = rows[0]
        body = rows[1:]
        parts = [
            f"Table on page {page_number}.",
            f"The table has {len(body)} rows and {len(headers)} columns.",
            f"Column headers: {', '.join(h for h in headers if h) or 'unlabeled'}.",
        ]
        for idx, row in enumerate(body[:3], start=1):
            cells = [f"{headers[col] or f'col{col+1}'}={value}" for col, value in enumerate(row)]
            parts.append(f"Row {idx}: " + ", ".join(cells) + ".")
        return " ".join(parts)

    @staticmethod
    def _has_numeric_data(rows: list[list[str]]) -> bool:
        values = [cell for row in rows[1:] for cell in row]
        if not values:
            return False
        numeric = sum(1 for v in values if re.search(r"\d", v))
        return (numeric / max(1, len(values))) >= 0.4
