from __future__ import annotations

import re
from hashlib import sha1
from typing import Iterable

from research_rag.domain import Chunk, SourcePage

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    collapsed = "\n".join(line for line in lines if line)
    return re.sub(r"[ \t]+", " ", collapsed).strip()


def _tail_words(text: str, count: int) -> str:
    if count <= 0:
        return ""
    words = text.split()
    return " ".join(words[-count:])


def _split_oversized_sentence(sentence: str, chunk_size: int) -> list[str]:
    words = sentence.split()
    if len(words) <= chunk_size:
        return [sentence]

    windows: list[str] = []
    start = 0
    while start < len(words):
        window = words[start : start + chunk_size]
        windows.append(" ".join(window))
        start += chunk_size
    return windows


def _sentence_units(text: str, chunk_size: int) -> list[str]:
    sentences = [part.strip() for part in _SENTENCE_SPLIT.split(text) if part.strip()]
    units: list[str] = []
    for sentence in sentences:
        units.extend(_split_oversized_sentence(sentence, chunk_size))
    if not units and text:
        units.extend(_split_oversized_sentence(text, chunk_size))
    return units


def chunk_pages(
    document_id: str,
    pages: Iterable[SourcePage],
    chunk_size: int,
    chunk_overlap: int,
) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be between 0 and chunk_size - 1")

    chunks: list[Chunk] = []
    ordinal = 0

    for page in pages:
        text = normalize_text(page.text)
        if not text:
            continue

        units = _sentence_units(text, chunk_size)
        current = ""
        current_word_count = 0

        for unit in units:
            unit = unit.strip()
            if not unit:
                continue

            unit_words = len(unit.split())
            if current and current_word_count + unit_words > chunk_size:
                chunks.append(_build_chunk(document_id, ordinal, page.page_number, current))
                ordinal += 1

                overlap_seed = _tail_words(current, chunk_overlap)
                overlap_count = len(overlap_seed.split()) if overlap_seed else 0
                if overlap_count + unit_words > chunk_size:
                    current = unit
                    current_word_count = unit_words
                else:
                    current = f"{overlap_seed} {unit}".strip() if overlap_seed else unit
                    current_word_count = overlap_count + unit_words
                continue

            current = f"{current} {unit}".strip() if current else unit
            current_word_count = len(current.split())

        if current:
            chunks.append(_build_chunk(document_id, ordinal, page.page_number, current))
            ordinal += 1

    return chunks


def _build_chunk(document_id: str, ordinal: int, page_number: int, text: str) -> Chunk:
    digest = sha1(f"{document_id}:{page_number}:{ordinal}:{text}".encode("utf-8")).hexdigest()
    return Chunk(
        chunk_id=digest,
        document_id=document_id,
        ordinal=ordinal,
        page_number=page_number,
        text=text,
        token_count=len(text.split()),
        metadata={"page_number": page_number},
    )
