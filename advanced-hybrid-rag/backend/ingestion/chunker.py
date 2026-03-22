"""Chunking strategies for research documents."""

from __future__ import annotations

import re
from uuid import uuid4

from .models import Chunk, ChunkMetadata, ProcessedDocument, Section


class SmartChunker:
	"""Create chunks with multiple strategy options."""

	def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64, semantic_threshold: float = 0.7) -> None:
		self.chunk_size = chunk_size
		self.chunk_overlap = chunk_overlap
		self.semantic_threshold = semantic_threshold

	def chunk_document(self, doc: ProcessedDocument, strategy: str = "section") -> list[Chunk]:
		"""Chunk an entire processed document using a selected strategy."""
		if strategy == "recursive":
			base_chunks = self._chunk_recursive_text(doc.raw_text, section_name="Document", page_start=1, page_end=1)
		elif strategy == "semantic":
			base_chunks = self._chunk_semantic_text(doc.raw_text, section_name="Document", page_start=1, page_end=1)
		elif strategy == "sliding":
			base_chunks = self._chunk_sliding_text(doc.raw_text, section_name="Document", page_start=1, page_end=1)
		else:
			base_chunks = self._chunk_section_aware(doc)

		total = len(base_chunks)
		for idx, chunk in enumerate(base_chunks):
			chunk.metadata.doc_id = doc.metadata.doc_id
			chunk.metadata.source_file = doc.metadata.source
			chunk.metadata.chunk_index = idx
			chunk.metadata.total_chunks = total
		return base_chunks

	def _chunk_section_aware(self, doc: ProcessedDocument) -> list[Chunk]:
		chunks: list[Chunk] = []
		sections = doc.sections or [Section(name="Document", text=doc.raw_text, page_start=1, page_end=1)]
		for section in sections:
			name = section.name.lower()
			if name == "abstract" and len(section.text) <= self.chunk_size * 2:
				chunks.extend(self._create_chunks_from_text(section.text, section.name, section.page_start, section.page_end))
				continue
			if any(token in name for token in ["method", "result", "discussion", "experiment"]):
				chunks.extend(self._chunk_recursive_text(section.text, section.name, section.page_start, section.page_end))
			else:
				chunks.extend(self._create_chunks_from_text(section.text, section.name, section.page_start, section.page_end))

		if doc.figures:
			for fig in doc.figures:
				chunks.append(
					Chunk(
						text=fig.caption,
						metadata=ChunkMetadata(
							doc_id=doc.metadata.doc_id,
							chunk_id=f"chunk-{uuid4().hex}",
							source_file=doc.metadata.source,
							section="Figure Caption",
							page_start=fig.page,
							page_end=fig.page,
							char_start=0,
							char_end=len(fig.caption),
							chunk_index=0,
							total_chunks=0,
							is_caption=True,
						),
					)
				)
		return chunks

	def _chunk_recursive_text(self, text: str, section_name: str, page_start: int, page_end: int) -> list[Chunk]:
		splitters = ["\n\n", "\n", ". ", " "]
		parts = [text]
		for splitter in splitters:
			next_parts: list[str] = []
			for part in parts:
				if len(part) <= self.chunk_size:
					next_parts.append(part)
				else:
					next_parts.extend(self._split_keep_delim(part, splitter))
			parts = next_parts
		merged = self._merge_small_parts(parts)
		return self._create_chunks_from_parts(merged, section_name, page_start, page_end)

	def _chunk_semantic_text(self, text: str, section_name: str, page_start: int, page_end: int) -> list[Chunk]:
		sentences = re.split(r"(?<=[.!?])\s+", text)
		if len(sentences) <= 1:
			return self._create_chunks_from_text(text, section_name, page_start, page_end)

		similarities = self._adjacent_sentence_similarity(sentences)
		current = [sentences[0]]
		segments: list[str] = []
		for idx, sentence in enumerate(sentences[1:], start=0):
			if similarities[idx] < self.semantic_threshold and len(" ".join(current)) >= 100:
				segments.append(" ".join(current))
				current = [sentence]
			else:
				current.append(sentence)
		if current:
			segments.append(" ".join(current))
		segments = self._merge_small_parts(segments, min_size=100)
		return self._create_chunks_from_parts(segments, section_name, page_start, page_end)

	def _chunk_sliding_text(self, text: str, section_name: str, page_start: int, page_end: int) -> list[Chunk]:
		words = text.split()
		if not words:
			return []
		window = max(16, self.chunk_size)
		step = max(8, window - self.chunk_overlap)
		parts: list[str] = []
		for start in range(0, len(words), step):
			part = " ".join(words[start : start + window])
			if part:
				parts.append(part)
		return self._create_chunks_from_parts(parts, section_name, page_start, page_end)

	def _create_chunks_from_text(self, text: str, section_name: str, page_start: int, page_end: int) -> list[Chunk]:
		return self._create_chunks_from_parts([text], section_name, page_start, page_end)

	def _create_chunks_from_parts(
		self,
		parts: list[str],
		section_name: str,
		page_start: int,
		page_end: int,
	) -> list[Chunk]:
		chunks: list[Chunk] = []
		cursor = 0
		for part in parts:
			clean = part.strip()
			if not clean:
				continue
			start = cursor
			end = cursor + len(clean)
			cursor = end + 1
			chunks.append(
				Chunk(
					text=clean,
					metadata=ChunkMetadata(
						doc_id="",
						chunk_id=f"chunk-{uuid4().hex}",
						source_file="",
						section=section_name,
						page_start=page_start,
						page_end=page_end,
						char_start=start,
						char_end=end,
						chunk_index=0,
						total_chunks=0,
					),
				)
			)
		return chunks

	def _split_keep_delim(self, text: str, splitter: str) -> list[str]:
		if splitter == " ":
			return text.split(splitter)
		if splitter == ". ":
			pieces = [p.strip() for p in text.split(splitter)]
			return [f"{p}." if not p.endswith(".") else p for p in pieces if p]
		return [p for p in text.split(splitter) if p]

	def _merge_small_parts(self, parts: list[str], min_size: int = 80) -> list[str]:
		merged: list[str] = []
		buffer = ""
		for part in parts:
			candidate = f"{buffer} {part}".strip()
			if len(candidate) < min_size:
				buffer = candidate
				continue
			merged.append(candidate)
			buffer = ""
		if buffer:
			merged.append(buffer)
		return merged

	def _adjacent_sentence_similarity(self, sentences: list[str]) -> list[float]:
		try:
			from sentence_transformers import SentenceTransformer

			model = SentenceTransformer("all-MiniLM-L6-v2")
			emb = model.encode(sentences, normalize_embeddings=True)
			sims: list[float] = []
			for idx in range(len(sentences) - 1):
				sims.append(float((emb[idx] * emb[idx + 1]).sum()))
			return sims
		except Exception:
			sims = []
			for idx in range(len(sentences) - 1):
				a = set(re.findall(r"\w+", sentences[idx].lower()))
				b = set(re.findall(r"\w+", sentences[idx + 1].lower()))
				union = len(a | b) or 1
				sims.append(len(a & b) / union)
			return sims


__all__ = ["SmartChunker"]
