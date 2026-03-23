from __future__ import annotations

import logging
from pathlib import Path

from research_rag.hybrid.engines.document_understanding import (
    BBoxTextReconstructor,
    clean_extracted_text,
    extraction_quality_score,
)


logger = logging.getLogger(__name__)


class DoclingParser:
    def parse_pages(self, pdf_path: Path) -> list[dict[str, object]]:
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        document = result.document

        page_buckets: dict[int, list[str]] = {}
        for item in getattr(document, "texts", []):
            text = clean_extracted_text(str(getattr(item, "text", "") or ""))
            if not text:
                continue
            page_no = 1
            provenance = getattr(item, "prov", None) or []
            if provenance:
                page_no = int(getattr(provenance[0], "page_no", 1) or 1)
            page_buckets.setdefault(page_no, []).append(text)

        pages: list[dict[str, object]] = []
        for page_no in sorted(page_buckets):
            merged = "\n".join(page_buckets[page_no]).strip()
            pages.append(
                {
                    "page_number": page_no,
                    "text": merged,
                    "layout_columns": 1,
                    "extraction_quality_score": extraction_quality_score(merged),
                    "elements_by_type": {"paragraph": max(1, len(page_buckets[page_no]))},
                }
            )
        return pages


class MarkerParser:
    def __init__(self) -> None:
        from marker.models import load_all_models

        self._models = load_all_models()

    def parse_pages(self, pdf_path: Path) -> list[dict[str, object]]:
        from marker.convert import convert_single_pdf

        markdown, _images, metadata = convert_single_pdf(
            str(pdf_path),
            self._models,
            max_pages=None,
            langs=["English"],
        )
        text = clean_extracted_text(str(markdown or ""))
        page_count = int(getattr(metadata, "page_count", 1) or 1) if metadata else 1
        return [
            {
                "page_number": idx,
                "text": text if idx == 1 else "",
                "layout_columns": 1,
                "extraction_quality_score": extraction_quality_score(text),
                "elements_by_type": {"paragraph": max(1, len([line for line in text.splitlines() if line.strip()]))},
            }
            for idx in range(1, page_count + 1)
        ]


class SmartPDFProcessor:
    def __init__(
        self,
        enable_pdfplumber: bool = True,
        enable_docling: bool = True,
        enable_marker: bool = True,
    ) -> None:
        self.enable_pdfplumber = enable_pdfplumber
        self.enable_docling = enable_docling
        self.enable_marker = enable_marker
        self._bbox = BBoxTextReconstructor()

    def process(self, pdf_path: Path) -> list[dict[str, object]]:
        if self.enable_docling:
            try:
                docling_pages = DoclingParser().parse_pages(pdf_path)
                if self._avg_quality(docling_pages) > 0.75:
                    return docling_pages
                logger.info("Docling extraction quality below threshold, trying marker parser")
            except Exception as exc:  # pragma: no cover - optional dependency/runtime
                logger.warning("Docling parser failed, falling back: %s", exc)

        if self.enable_marker:
            try:
                marker_pages = MarkerParser().parse_pages(pdf_path)
                if self._avg_quality(marker_pages) > 0.65:
                    return marker_pages
                logger.info("Marker extraction quality below threshold, trying bbox parser")
            except Exception as exc:  # pragma: no cover - optional dependency/runtime
                logger.warning("Marker parser failed, falling back: %s", exc)

        try:
            bbox_pages = self._bbox.process_pdf(pdf_path)
        except Exception as exc:
            logger.warning("BBox parser failed, falling back to legacy extraction: %s", exc)
            bbox_pages = []

        if bbox_pages and self._avg_quality(bbox_pages) > 0.55:
            return bbox_pages
        return self._legacy_extract(pdf_path)

    def _legacy_extract(self, pdf_path: Path) -> list[dict[str, object]]:
        if self.enable_pdfplumber:
            try:
                import pdfplumber

                with pdfplumber.open(str(pdf_path)) as pdf:
                    pages = []
                    for idx, page in enumerate(pdf.pages, start=1):
                        text = self._extract_page_text(page)
                        pages.append(
                            {
                                "page_number": idx,
                                "text": text,
                                "layout_columns": 1,
                                "extraction_quality_score": extraction_quality_score(text),
                                "elements_by_type": {"paragraph": max(1, len([line for line in text.splitlines() if line.strip()]))},
                            }
                        )
                    if any((page["text"] or "").strip() for page in pages):
                        return pages
            except ModuleNotFoundError:
                pass

        try:
            from pypdf import PdfReader
        except ModuleNotFoundError as exc:
            raise RuntimeError("PDF parsing requires pdfplumber, pypdf, or optional smart parsers.") from exc

        reader = PdfReader(str(pdf_path))
        pages = []
        for idx, page in enumerate(reader.pages, start=1):
            text = clean_extracted_text(page.extract_text() or "")
            pages.append(
                {
                    "page_number": idx,
                    "text": text,
                    "layout_columns": 1,
                    "extraction_quality_score": extraction_quality_score(text),
                    "elements_by_type": {"paragraph": max(1, len([line for line in text.splitlines() if line.strip()]))},
                }
            )
        return pages

    @staticmethod
    def _avg_quality(pages: list[dict[str, object]]) -> float:
        if not pages:
            return 0.0
        values = [float(page.get("extraction_quality_score", 0.0) or 0.0) for page in pages]
        return sum(values) / len(values)

    @staticmethod
    def _extract_page_text(page) -> str:
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
            return clean_extracted_text("\n".join(line for line in ordered if line.strip()))
        return clean_extracted_text(page.extract_text() or "")


class PDFParser:
    def __init__(
        self,
        enable_pdfplumber: bool = True,
        enable_docling: bool = True,
        enable_marker: bool = True,
    ) -> None:
        self.processor = SmartPDFProcessor(
            enable_pdfplumber=enable_pdfplumber,
            enable_docling=enable_docling,
            enable_marker=enable_marker,
        )

    def parse_pages(self, pdf_path: Path) -> list[dict[str, object]]:
        return self.processor.process(pdf_path)
