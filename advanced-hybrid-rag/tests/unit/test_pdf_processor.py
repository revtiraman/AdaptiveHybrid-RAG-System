from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.ingestion.pdf_processor import PDFProcessor


def _find_attention_pdf() -> Path | None:
	candidates = []
	env_path = os.getenv("ATTENTION_PDF_PATH")
	if env_path:
		candidates.append(Path(env_path))
	candidates.extend(Path.cwd().glob("**/*attention*all*you*need*.pdf"))
	downloads = Path.home() / "Downloads"
	if downloads.exists():
		candidates.extend(downloads.glob("*attention*all*you*need*.pdf"))
	for path in candidates:
		if path.exists() and path.is_file():
			return path
	return None


def _avg_word_length(text: str) -> float:
	words = re.findall(r"[A-Za-z]+", text)
	if not words:
		return 0.0
	return sum(len(w) for w in words) / len(words)


def test_attention_pdf_text_spacing_and_word_length():
	pdf_path = _find_attention_pdf()
	if pdf_path is None:
		pytest.skip("Attention Is All You Need PDF not found. Set ATTENTION_PDF_PATH to run this test.")

	processor = PDFProcessor()
	processed = processor.process(pdf_path)
	text = processed.raw_text.lower()

	assert "attention mechanism" in text
	avg_len = _avg_word_length(processed.raw_text)
	assert 3 <= avg_len <= 12


def test_attention_pdf_references_not_mislabeled_as_conclusion():
	pdf_path = _find_attention_pdf()
	if pdf_path is None:
		pytest.skip("Attention Is All You Need PDF not found. Set ATTENTION_PDF_PATH to run this test.")

	processor = PDFProcessor()
	processed = processor.process(pdf_path)

	reference_sections = [s for s in processed.sections if s.name == "references"]
	assert reference_sections, "No references section detected"
	assert any("[12]" in s.text for s in reference_sections)

	conclusion_sections = [s for s in processed.sections if s.name == "conclusion"]
	assert all("[12]" not in s.text for s in conclusion_sections)
