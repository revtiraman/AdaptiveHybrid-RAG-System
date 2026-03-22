from __future__ import annotations

from pathlib import Path

from research_rag.domain import SourcePage


class PdfLoader:
    def load_pages(self, pdf_path: Path) -> list[SourcePage]:
        try:
            from pypdf import PdfReader
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "PDF ingestion requires pypdf. Install dependencies with `pip install -e .` first."
            ) from exc

        reader = PdfReader(str(pdf_path))
        pages: list[SourcePage] = []
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append(SourcePage(page_number=index, text=text, metadata={"page_number": index}))
        return pages
