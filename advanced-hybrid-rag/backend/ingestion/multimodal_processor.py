"""Multi-modal document processing (figures/tables/equations)."""

from __future__ import annotations

import re
from pathlib import Path

from .models import Figure, Table


class MultimodalProcessor:
    """Extract multimodal artifacts from PDFs and convert to extra chunks."""

    def extract_figures(self, file_path: str | Path) -> list[Figure]:
        try:
            import fitz  # type: ignore

            doc = fitz.open(file_path)
            figures: list[Figure] = []
            for i, page in enumerate(doc, start=1):
                text = page.get_text("text")
                for m in re.finditer(r"(?im)^(figure\s*\d+[:.\-].+)$", text):
                    figures.append(Figure(page=i, caption=m.group(1).strip()))
            return figures
        except Exception:
            return []

    def extract_tables(self, file_path: str | Path) -> list[Table]:
        try:
            import pdfplumber  # type: ignore

            out: list[Table] = []
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    for tab in page.extract_tables() or []:
                        out.append(Table(page=i, rows=[[c or "" for c in row] for row in tab if row]))
            return out
        except Exception:
            return []

    def detect_equations(self, text: str) -> list[str]:
        patterns = [r"\$[^$]{2,300}\$", r"\\\[[\s\S]{2,500}?\\\]"]
        eqs: list[str] = []
        for p in patterns:
            eqs.extend(re.findall(p, text))
        return eqs


__all__ = ["MultimodalProcessor"]
