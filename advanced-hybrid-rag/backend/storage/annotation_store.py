"""Annotation storage for collaborative notes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Annotation:
    doc_id: str
    chunk_id: str
    text: str
    annotation: str
    user_id: str
    public: bool = False


class AnnotationStore:
    """In-memory annotation storage backend."""

    def __init__(self) -> None:
        self.items: list[Annotation] = []

    def add(self, ann: Annotation) -> None:
        self.items.append(ann)

    def by_doc(self, doc_id: str) -> list[Annotation]:
        return [a for a in self.items if a.doc_id == doc_id]

    def search(self, term: str) -> list[Annotation]:
        t = term.lower()
        return [a for a in self.items if t in a.annotation.lower() or t in a.text.lower()]


__all__ = ["Annotation", "AnnotationStore"]
