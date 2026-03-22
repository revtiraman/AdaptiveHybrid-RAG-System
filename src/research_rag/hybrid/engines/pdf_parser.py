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
                        text = self._extract_page_text(page)
                        pages.append({"page_number": idx, "text": text})
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

    @staticmethod
    def _extract_page_text(page) -> str:
        # Word-level extraction usually preserves spaces better than raw text on dense PDFs.
        words = page.extract_words(use_text_flow=True, keep_blank_chars=False)
        if words:
            lines: dict[int, list[str]] = {}
            for item in words:
                token = str(item.get("text", "")).strip()
                if not token:
                    continue
                top = int(round(float(item.get("top", 0.0))))
                lines.setdefault(top, []).append(token)
            ordered = [" ".join(tokens) for _, tokens in sorted(lines.items(), key=lambda pair: pair[0])]
            return "\n".join(line for line in ordered if line.strip())
        return page.extract_text() or ""
