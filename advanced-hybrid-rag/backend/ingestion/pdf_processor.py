"""PDF processing engine for research-paper ingestion."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from uuid import uuid4

from .models import DocumentMetadata, Figure, ProcessedDocument, Reference, Section, Table


SECTION_PATTERNS = [
	r"^abstract$",
	r"^introduction$",
	r"^related\s+work$",
	r"^background$",
	r"^method(?:ology|s)?$",
	r"^experiments?$",
	r"^results?$",
	r"^discussion$",
	r"^conclusion$",
	r"^references$",
	r"^appendix$",
]


class PDFProcessor:
	"""Extract structured paper content from PDF files."""

	def process(self, file_path: str | Path) -> ProcessedDocument:
		"""Process a PDF into normalized text, sections, and metadata."""
		path = Path(file_path)
		raw_text, page_texts = self._extract_with_pymupdf(path)
		if not raw_text.strip():
			raw_text, page_texts = self._extract_with_pypdf(path)

		raw_text = self._clean_text(raw_text)
		tables = self._extract_tables(path)
		figures = self._extract_figure_captions(page_texts)
		sections = self._detect_sections(page_texts)
		metadata = self._extract_metadata(path, page_texts)
		metadata.language = self.detect_language(raw_text)
		references = self.extract_references(raw_text)
		equations = self.extract_math_equations(raw_text)

		return ProcessedDocument(
			raw_text=raw_text,
			sections=sections,
			metadata=metadata,
			tables=tables,
			figures=figures,
			references=references,
			math_equations=equations,
		)

	def detect_language(self, text: str) -> str:
		"""Best-effort language detection with safe fallback."""
		try:
			from langdetect import detect  # type: ignore

			return detect(text[:5000])
		except Exception:
			return "unknown"

	def extract_references(self, text: str) -> list[Reference]:
		"""Parse bibliography-like lines into reference objects."""
		refs_match = re.search(r"(?im)^references\s*$", text)
		if not refs_match:
			return []
		refs_text = text[refs_match.end() :]
		lines = [ln.strip() for ln in refs_text.splitlines() if ln.strip()]
		refs: list[Reference] = []
		for line in lines[:300]:
			year_match = re.search(r"(19|20)\d{2}", line)
			refs.append(
				Reference(
					raw=line,
					year=int(year_match.group()) if year_match else None,
				)
			)
		return refs

	def extract_math_equations(self, text: str) -> list[str]:
		"""Extract LaTeX-like equation snippets from text."""
		patterns = [
			r"\$[^$]{2,200}\$",
			r"\\\[[\s\S]{2,200}?\\\]",
			r"\\begin\{equation\}[\s\S]{2,500}?\\end\{equation\}",
		]
		eqs: list[str] = []
		for pattern in patterns:
			eqs.extend(re.findall(pattern, text))
		return eqs

	def _extract_with_pymupdf(self, file_path: Path) -> tuple[str, list[str]]:
		"""Primary extractor using pymupdf for layout-heavy documents."""
		try:
			import fitz  # type: ignore

			doc = fitz.open(file_path)
			pages: list[str] = []
			for page in doc:
				pages.append(page.get_text("text"))
			return "\n\n".join(pages), pages
		except Exception:
			return "", []

	def _extract_with_pypdf(self, file_path: Path) -> tuple[str, list[str]]:
		"""Fallback extractor using pypdf when richer parsers fail."""
		try:
			from pypdf import PdfReader  # type: ignore

			reader = PdfReader(str(file_path))
			pages = [(pg.extract_text() or "") for pg in reader.pages]
			return "\n\n".join(pages), pages
		except Exception:
			return "", []

	def _extract_tables(self, file_path: Path) -> list[Table]:
		"""Extract tables with pdfplumber as a specialized fallback."""
		tables: list[Table] = []
		try:
			import pdfplumber  # type: ignore

			with pdfplumber.open(file_path) as pdf:
				for idx, page in enumerate(pdf.pages, start=1):
					page_tables = page.extract_tables() or []
					for tab in page_tables:
						rows = [[cell or "" for cell in row] for row in tab if row]
						tables.append(Table(page=idx, rows=rows))
		except Exception:
			return []
		return tables

	def _extract_figure_captions(self, page_texts: list[str]) -> list[Figure]:
		"""Find figure captions using Figure N heuristic."""
		figures: list[Figure] = []
		for idx, text in enumerate(page_texts, start=1):
			for match in re.finditer(r"(?im)^(figure\s*\d+[:.\-].+)$", text):
				figures.append(Figure(page=idx, caption=match.group(1).strip()))
		return figures

	def _detect_sections(self, page_texts: list[str]) -> list[Section]:
		"""Split document into logical sections based on heading patterns."""
		full = "\n".join(page_texts)
		lines = full.splitlines()
		sections: list[Section] = []

		current_name = "Unknown"
		current_start = 1
		buf: list[str] = []

		def flush(end_line: int) -> None:
			if not buf:
				return
			section_text = "\n".join(buf).strip()
			if section_text:
				sections.append(
					Section(
						name=current_name,
						text=section_text,
						page_start=current_start,
						page_end=max(current_start, end_line),
					)
				)

		for i, line in enumerate(lines, start=1):
			normalized = re.sub(r"\s+", " ", line.strip()).lower()
			is_heading = any(re.match(pattern, normalized) for pattern in SECTION_PATTERNS)
			if is_heading:
				flush(i)
				current_name = line.strip().title()
				current_start = i
				buf = []
				continue
			buf.append(line)

		flush(len(lines))
		return sections if sections else [Section(name="Document", text=full, page_start=1, page_end=max(1, len(page_texts)))]

	def _extract_metadata(self, file_path: Path, page_texts: list[str]) -> DocumentMetadata:
		"""Heuristic metadata extraction from title page and text patterns."""
		first_page = page_texts[0] if page_texts else ""
		lines = [ln.strip() for ln in first_page.splitlines() if ln.strip()]

		title = lines[0] if lines else file_path.stem
		authors = re.split(r",| and ", lines[1]) if len(lines) > 1 else []
		authors = [a.strip() for a in authors if a.strip()]

		full = "\n".join(page_texts)
		doi_match = re.search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", full, flags=re.I)
		year_match = re.search(r"\b(19|20)\d{2}\b", first_page)
		venue_match = re.search(
			r"(?i)\b(neurips|icml|iclr|acl|emnlp|cvpr|eccv|aaai|ijcai|kdd|www|sigir)\b",
			first_page,
		)

		return DocumentMetadata(
			doc_id=f"doc-{uuid4().hex}",
			source=str(file_path),
			title=title,
			authors=authors,
			doi=doi_match.group(0) if doi_match else None,
			year=int(year_match.group(0)) if year_match else None,
			venue=venue_match.group(0).upper() if venue_match else None,
		)

	def _clean_text(self, text: str) -> str:
		"""Normalize text artifacts commonly seen in extracted PDFs."""
		text = text.replace("\ufb01", "fi").replace("\ufb02", "fl")
		text = re.sub(r"-\n([a-z])", r"\1", text)
		text = re.sub(r"[ \t]+", " ", text)
		text = re.sub(r"\n{3,}", "\n\n", text)
		return unicodedata.normalize("NFKC", text).strip()


__all__ = ["PDFProcessor"]
