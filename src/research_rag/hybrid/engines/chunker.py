from __future__ import annotations

import re
from hashlib import sha1

from research_rag.hybrid.domain import SectionChunk
from research_rag.hybrid.utils import normalize_ws

_SECTION_PATTERNS = [
    ("abstract", re.compile(r"^\s*abstract\s*$", re.IGNORECASE)),
    ("introduction", re.compile(r"^\s*(\d+\.?\s*)?introduction\s*$", re.IGNORECASE)),
    ("related_work", re.compile(r"^\s*(\d+\.?\s*)?(related work|related works|prior work|background|literature review)\s*$", re.IGNORECASE)),
    ("method", re.compile(r"^\s*(\d+\.?\s*)?(method|methods|approach|methodology|proposed method|our approach|model|architecture|system|framework)\s*$", re.IGNORECASE)),
    ("experiments", re.compile(r"^\s*(\d+\.?\s*)?(experiments|experimental setup|experimental results|evaluation|setup|training|implementation details)\s*$", re.IGNORECASE)),
    ("results", re.compile(r"^\s*(\d+\.?\s*)?(results|analysis|ablation study|ablation|discussion|findings|performance)\s*$", re.IGNORECASE)),
    ("conclusion", re.compile(r"^\s*(\d+\.?\s*)?(conclusion|conclusions|concluding remarks|summary|future work|limitations and future work)\s*$", re.IGNORECASE)),
    ("limitations", re.compile(r"^\s*(\d+\.?\s*)?(limitations?|limitations and future work|broader impact|ethics|ethical considerations)\s*$", re.IGNORECASE)),
    ("references", re.compile(r"^\s*(references|bibliography|citations)\s*$", re.IGNORECASE)),
    ("appendix", re.compile(r"^\s*(appendix|supplementary|supplemental material|additional experiments)\s*$", re.IGNORECASE)),
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
            # Accumulate non-heading lines into paragraph blocks so that
            # sentences spanning multiple PDF lines are joined before splitting.
            pending_lines: list[str] = []
            for line in lines:
                normalized_line = self._clean_line_text(line)
                if not normalized_line:
                    # Blank line = paragraph boundary; flush pending lines
                    if pending_lines:
                        block = " ".join(pending_lines)
                        sentences_buffer.extend(self._split_sentences(block))
                        pending_lines = []
                    continue

                detected_section = self._detect_section_heading(normalized_line)
                if detected_section:
                    if pending_lines:
                        block = " ".join(pending_lines)
                        sentences_buffer.extend(self._split_sentences(block))
                        pending_lines = []
                    current_section = detected_section
                    continue

                pending_lines.append(normalized_line)

            # Flush any remaining lines at end of page
            if pending_lines:
                block = " ".join(pending_lines)
                sentences_buffer.extend(self._split_sentences(block))

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
            if any(token in title for token in ["intro", "motivation", "overview"]):
                return "introduction"
            if any(token in title for token in ["related", "background", "prior work", "literature"]):
                return "related_work"
            if any(token in title for token in ["method", "model", "architecture", "approach", "framework", "system", "proposed", "design"]):
                return "method"
            if any(token in title for token in ["experiment", "evaluation", "training", "setup", "implementation", "benchmark"]):
                return "experiments"
            if any(token in title for token in ["result", "analysis", "ablation", "discussion", "performance", "finding"]):
                return "results"
            if any(token in title for token in ["conclusion", "future work", "concluding", "summary"]):
                return "conclusion"
            if any(token in title for token in ["limitation", "broader impact", "ethical", "ethics"]):
                return "limitations"
            if any(token in title for token in ["appendix", "supplement"]):
                return "appendix"
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
