from __future__ import annotations

from pathlib import Path


class PDFParser:
    def __init__(self, enable_pdfplumber: bool = True) -> None:
        self.enable_pdfplumber = enable_pdfplumber

    def parse_pages(self, pdf_path: Path) -> list[dict[str, object]]:
        if self.enable_pdfplumber:
            try:
                import pdfplumber

                with pdfplumber.open(str(pdf_path)) as pdf:
                    pages = []
                    for idx, page in enumerate(pdf.pages, start=1):
                        pages.append({"page_number": idx, "text": page.extract_text() or ""})
                    if any((page["text"] or "").strip() for page in pages):
                        return pages
            except ModuleNotFoundError:
                pass

        try:
            from pypdf import PdfReader
        except ModuleNotFoundError as exc:
            raise RuntimeError("PDF parsing requires pdfplumber or pypdf.") from exc

        reader = PdfReader(str(pdf_path))
        return [
            {"page_number": idx, "text": page.extract_text() or ""}
            for idx, page in enumerate(reader.pages, start=1)
        ]
