from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from ingestion.chunker import SmartChunker
from ingestion.models import DocumentMetadata, Figure, ProcessedDocument, Section


def _doc(text: str) -> ProcessedDocument:
	return ProcessedDocument(
		raw_text=text,
		sections=[Section(name="Introduction", text=text, page_start=1, page_end=1)],
		metadata=DocumentMetadata(doc_id="d1", source="test", title="t"),
		figures=[Figure(page=1, caption="Figure 1: sample")],
	)


def test_recursive_chunking_respects_size():
	chunker = SmartChunker(chunk_size=60, chunk_overlap=10)
	doc = _doc(" ".join(["token"] * 220))
	chunks = chunker.chunk_document(doc, strategy="recursive")
	assert chunks
	assert all(len(c.text) <= 80 for c in chunks)


def test_semantic_chunking_finds_boundaries():
	chunker = SmartChunker(chunk_size=80, chunk_overlap=0)
	text = "Cats purr softly. Cats rest in sun. Quantum entanglement changes physics. Bell tests validate nonlocality."
	chunks = chunker.chunk_document(_doc(text), strategy="semantic")
	assert len(chunks) >= 2


def test_section_aware_never_crosses_sections():
	doc = ProcessedDocument(
		raw_text="A\nB",
		sections=[
			Section(name="Abstract", text="A", page_start=1, page_end=1),
			Section(name="Results", text="B", page_start=2, page_end=2),
		],
		metadata=DocumentMetadata(doc_id="d1", source="test"),
	)
	chunker = SmartChunker(chunk_size=40)
	chunks = chunker.chunk_document(doc, strategy="section")
	assert {c.metadata.section for c in chunks} >= {"Abstract", "Results"}


def test_chunk_metadata_preserved():
	chunker = SmartChunker(chunk_size=100)
	chunks = chunker.chunk_document(_doc("hello world"), strategy="section")
	assert chunks[0].metadata.doc_id == "d1"
	assert chunks[0].metadata.source_file == "test"


def test_overlap_correct():
	chunker = SmartChunker(chunk_size=20, chunk_overlap=5)
	chunks = chunker.chunk_document(_doc(" ".join(["word"] * 100)), strategy="sliding")
	assert len(chunks) > 1
