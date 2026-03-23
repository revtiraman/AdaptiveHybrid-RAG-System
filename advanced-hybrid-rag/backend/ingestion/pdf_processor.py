"""PDF processing engine for research-paper ingestion."""

from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path
from uuid import uuid4

from .models import DocumentMetadata, Figure, ProcessedDocument, Reference, Section, Table


logger = logging.getLogger(__name__)


SECTION_PATTERNS: list[tuple[str, str]] = [
	("references", r"^\s*references?\s*$"),
	("bibliography", r"^\s*bibliograph\w*\s*$"),
	("appendix", r"^\s*appendix\s*[a-z]?\s*$"),
	("conclusion", r"^\s*conclusions?\s*(and\s+future\s+work)?\s*$"),
	("discussion", r"^\s*discussion\s*$"),
	("results", r"^\s*(results|experiments?\s+and\s+results)\s*$"),
	("experiments", r"^\s*experiments?\s*$"),
	("method", r"^\s*(method(olog)?|approach|model)\s*$"),
	("related_work", r"^\s*related\s+work\s*$"),
	("introduction", r"^\s*introduction\s*$"),
	("abstract", r"^\s*abstract\s*$"),
]


EXCLUDED_FROM_RETRIEVAL = {"references", "bibliography", "acknowledgments"}


class PDFProcessor:
	"""Extract structured paper content from PDF files."""

	def process(self, file_path: str | Path) -> ProcessedDocument:
		"""Process a PDF into normalized text, sections, and metadata."""
		path = Path(file_path)
		raw_text, page_texts = self._extract_with_pymupdf(path)
		quality = self.detect_extraction_quality(raw_text)
		if raw_text.strip() and quality < 0.5:
			logger.warning("Low pymupdf extraction quality (%.3f) for %s. Trying pdfplumber fallback.", quality, path)
			plumber_text, plumber_pages = self._extract_with_pdfplumber_text(path)
			if plumber_text.strip() and self.detect_extraction_quality(plumber_text) >= quality:
				raw_text, page_texts = plumber_text, plumber_pages

		if not raw_text.strip():
			raw_text, page_texts = self._extract_with_pypdf(path)

		raw_text = self._clean_text(raw_text)
		tables = self._extract_tables(path)
		figures = self._extract_figure_captions(page_texts)
		sections = self.detect_sections(page_texts)
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
				# Trigger dict extraction path for robust layout-aware text reconstruction.
				_ = page.get_text("dict")
				pages.append(self._page_text_from_words(page.get_text("words")))
			return "\n\n".join(pages), pages
		except Exception:
			return "", []

	def _extract_with_pdfplumber_text(self, file_path: Path) -> tuple[str, list[str]]:
		"""Text extraction fallback via pdfplumber when quality is poor."""
		try:
			import pdfplumber  # type: ignore

			pages: list[str] = []
			with pdfplumber.open(file_path) as pdf:
				for page in pdf.pages:
					pages.append(page.extract_text() or "")
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

	def detect_sections(self, page_texts: list[str]) -> list[Section]:
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
				section_name = current_name
				if self._looks_like_references(section_text):
					section_name = "references"
				sections.append(
					Section(
						name=section_name,
						text=section_text,
						page_start=current_start,
						page_end=max(current_start, end_line),
					)
				)

		for i, line in enumerate(lines, start=1):
			normalized = re.sub(r"\s+", " ", line.strip())
			heading = self._match_section_heading(normalized)
			if heading:
				flush(i)
				current_name = heading
				current_start = i
				buf = []
				continue
			buf.append(line)

		flush(len(lines))
		return sections if sections else [Section(name="Document", text=full, page_start=1, page_end=max(1, len(page_texts)))]

	def _match_section_heading(self, line: str) -> str | None:
		for section_name, pattern in SECTION_PATTERNS:
			if re.match(pattern, line.strip(), flags=re.I):
				return section_name
		return None

	def _looks_like_references(self, section_text: str) -> bool:
		citation_lines = re.findall(r"\[\d+\]\s+[A-Z][a-z]+", section_text)
		numbered_refs = re.findall(r"(?m)^\s*\d+\.\s+[A-Z][a-z]+.+\(\d{4}\)", section_text)
		return (len(citation_lines) + len(numbered_refs)) >= 3

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
		text = (
			(text or "")
			.replace("ﬁ", "fi")
			.replace("ﬂ", "fl")
			.replace("ﬀ", "ff")
			.replace("ﬃ", "ffi")
		)
		text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
		text = unicodedata.normalize("NFKC", text)
		text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
		text = re.sub(r"  +", " ", text)
		text = re.sub(r"\n{3,}", "\n\n", text)
		return text.strip()

	def detect_extraction_quality(self, text: str) -> float:
		"""Score extracted text quality in [0, 1] using spacing and token sanity heuristics."""
		if not text:
			return 0.0

		total = max(1, len(text))
		space_ratio = text.count(" ") / total
		alpha_ratio = sum(1 for ch in text if ch.isalpha()) / total
		words = re.findall(r"[A-Za-z]+", text)
		avg_word_len = (sum(len(w) for w in words) / max(1, len(words))) if words else 0.0

		space_score = max(0.0, 1.0 - min(1.0, abs(space_ratio - 0.17) / 0.17))
		alpha_score = min(1.0, alpha_ratio / 0.6)
		if 3.0 <= avg_word_len <= 8.0:
			word_score = 1.0
		elif 2.0 <= avg_word_len <= 12.0:
			word_score = 0.6
		else:
			word_score = 0.2

		score = (0.4 * space_score) + (0.35 * alpha_score) + (0.25 * word_score)
		return float(max(0.0, min(1.0, score)))

	def _page_text_from_words(self, words: list[tuple]) -> str:
		if not words:
			return ""

		sorted_words = sorted(words, key=lambda w: (int(w[5]), int(w[6]), int(w[7])))
		lines: list[str] = []
		current_line_key: tuple[int, int] | None = None
		current_parts: list[str] = []
		prev_x1: float | None = None

		for word in sorted_words:
			x0, _y0, x1, _y1, token, block_num, line_num, _word_num = word
			if not isinstance(token, str) or not token.strip():
				continue

			line_key = (int(block_num), int(line_num))
			if current_line_key != line_key:
				if current_parts:
					lines.append("".join(current_parts).strip())
				current_parts = [token.strip()]
				current_line_key = line_key
				prev_x1 = float(x1)
				continue

			x_gap = float(x0) - float(prev_x1 or x0)
			if x_gap > 1.5:
				current_parts.append(" ")
			current_parts.append(token.strip())
			prev_x1 = float(x1)

		if current_parts:
			lines.append("".join(current_parts).strip())

		return "\n".join(line for line in lines if line)


__all__ = ["PDFProcessor"]
