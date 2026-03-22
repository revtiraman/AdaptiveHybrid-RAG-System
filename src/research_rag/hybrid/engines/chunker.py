from __future__ import annotations

import re
from hashlib import sha1

from research_rag.hybrid.domain import SectionChunk
from research_rag.hybrid.utils import normalize_ws

_SECTION_PATTERNS = [
    ("abstract", re.compile(r"^\s*abstract\s*$", re.IGNORECASE)),
    ("introduction", re.compile(r"^\s*(1\.?\s*)?introduction\s*$", re.IGNORECASE)),
    ("related_work", re.compile(r"^\s*(2\.?\s*)?(related work|background)\s*$", re.IGNORECASE)),
    ("method", re.compile(r"^\s*(3\.?\s*)?(method|approach|methodology)\s*$", re.IGNORECASE)),
    ("experiments", re.compile(r"^\s*(4\.?\s*)?(experiments|evaluation)\s*$", re.IGNORECASE)),
    ("results", re.compile(r"^\s*(5\.?\s*)?(results|discussion)\s*$", re.IGNORECASE)),
    ("conclusion", re.compile(r"^\s*(6\.?\s*)?conclusion[s]?\s*$", re.IGNORECASE)),
]

_NUMBERED_HEADING = re.compile(r"^\s*(\d+(?:\.\d+)*)\s+([A-Za-z][A-Za-z0-9\- ]{2,80})\s*$")


class SectionAwareChunker:
    def __init__(self, chunk_chars: int = 200, overlap: int = 40) -> None:
        if chunk_chars <= 0:
            raise ValueError("chunk_chars must be positive")
        if overlap < 0 or overlap >= chunk_chars:
            raise ValueError("overlap must be between 0 and chunk_chars - 1")
        self.chunk_chars = chunk_chars
        self.overlap = overlap

    def chunk_document(self, paper_id: str, pages: list[dict[str, object]]) -> list[SectionChunk]:
        chunks: list[SectionChunk] = []
        current_section = "body"
        ordinal = 0

        for page in pages:
            page_number = int(page["page_number"])
            lines = str(page["text"] or "").splitlines()

            sentences_buffer: list[str] = []
            for line in lines:
                normalized_line = self._clean_line_text(line)
                if not normalized_line:
                    continue

                detected_section = self._detect_section_heading(normalized_line)
                if detected_section:
                    current_section = detected_section
                    continue

                sentences_buffer.extend(self._split_sentences(normalized_line))

            for chunk_text in self._build_sentence_chunks(sentences_buffer):
                chunks.append(self._build_chunk(paper_id, page_number, current_section, ordinal, chunk_text))
                ordinal += 1

        return chunks

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        parts = re.split(r"(?<=[.!?])\s*", text)
        sentences = [part.strip() for part in parts if part.strip()]
        return sentences or [text]

    @staticmethod
    def _clean_line_text(text: str) -> str:
        cleaned = normalize_ws(text)
        if not cleaned:
            return ""
        # Repair common PDF extraction artifacts such as missing spaces after punctuation.
        cleaned = re.sub(r"([.!?;:,])([A-Z])", r"\1 \2", cleaned)
        # Split lower->Upper transitions that frequently appear in extracted PDF text.
        cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", cleaned)
        return normalize_ws(cleaned)

    def _build_sentence_chunks(self, sentences: list[str]) -> list[str]:
        if not sentences:
            return []

        chunks: list[str] = []
        current = ""

        for sentence in sentences:
            if len(sentence) > self.chunk_chars:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.extend(self._split_long_sentence(sentence))
                continue

            candidate = f"{current} {sentence}".strip() if current else sentence
            if len(candidate) <= self.chunk_chars:
                current = candidate
                continue

            chunks.append(current)
            overlap_seed = self._tail_words(current)
            current = f"{overlap_seed} {sentence}".strip() if overlap_seed else sentence

        if current:
            chunks.append(current)

        return [chunk for chunk in chunks if chunk.strip()]

    def _split_long_sentence(self, sentence: str) -> list[str]:
        words = sentence.split()
        if not words:
            return []

        output: list[str] = []
        current_words: list[str] = []
        for word in words:
            candidate = " ".join(current_words + [word]).strip()
            if candidate and len(candidate) <= self.chunk_chars:
                current_words.append(word)
                continue

            if current_words:
                output.append(" ".join(current_words))
                seed = self._tail_words(" ".join(current_words))
                current_words = seed.split() if seed else []

            current_words.append(word)

        if current_words:
            output.append(" ".join(current_words))
        return output

    def _tail_words(self, text: str) -> str:
        if self.overlap <= 0:
            return ""
        words = text.split()
        if not words:
            return ""

        selected: list[str] = []
        length = 0
        for word in reversed(words):
            increment = len(word) + (1 if selected else 0)
            if length + increment > self.overlap:
                break
            selected.append(word)
            length += increment
        return " ".join(reversed(selected))

    @staticmethod
    def _detect_section_heading(line: str) -> str | None:
        if len(line.split()) > 8:
            return None
        for section, pattern in _SECTION_PATTERNS:
            if pattern.match(line):
                return section

        numbered = _NUMBERED_HEADING.match(line)
        if numbered:
            title = numbered.group(2).strip().lower()
            if any(token in title for token in ["intro", "motivation"]):
                return "introduction"
            if any(token in title for token in ["related", "background"]):
                return "related_work"
            if any(token in title for token in ["method", "model", "architecture", "approach"]):
                return "method"
            if any(token in title for token in ["experiment", "evaluation", "training"]):
                return "experiments"
            if any(token in title for token in ["result", "analysis", "discussion"]):
                return "results"
            if any(token in title for token in ["conclusion", "future work"]):
                return "conclusion"
        return None

    @staticmethod
    def _build_chunk(paper_id: str, page_number: int, section: str, ordinal: int, text: str) -> SectionChunk:
        key = f"{paper_id}:{page_number}:{section}:{ordinal}:{text}"
        chunk_id = sha1(key.encode("utf-8")).hexdigest()
        return SectionChunk(
            chunk_id=chunk_id,
            paper_id=paper_id,
            page_number=page_number,
            section=section,
            ordinal=ordinal,
            text=text,
            char_count=len(text),
            metadata={"section": section, "page_number": page_number},
        )
