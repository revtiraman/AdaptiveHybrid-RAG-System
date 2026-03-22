from __future__ import annotations

# pyright: reportMissingImports=false

from typing import Any

from research_rag.hybrid.config import HybridRAGSettings
from research_rag.hybrid.domain import SectionChunk


class VectorStore:
    def __init__(self, settings: HybridRAGSettings) -> None:
        self.settings = settings
        self._client = None
        self._collection = None

    def initialize(self) -> None:
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
        except ModuleNotFoundError as exc:
            raise RuntimeError("ChromaDB is required. Install project dependencies.") from exc

        self._client = chromadb.PersistentClient(
            path=str(self.settings.chroma_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(name=self.settings.chroma_collection)

    def upsert(self, chunks: list[SectionChunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        if self._collection is None:
            raise RuntimeError("Vector store not initialized")

        self._collection.upsert(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "paper_id": c.paper_id,
                    "section": c.section,
                    "page_number": c.page_number,
                    "ordinal": c.ordinal,
                }
                for c in chunks
            ],
        )

    def query(self, query_vector: list[float], top_k: int, paper_ids: list[str] | None = None) -> list[dict[str, Any]]:
        if self._collection is None:
            raise RuntimeError("Vector store not initialized")

        where = None
        if paper_ids:
            where = {"paper_id": {"$in": paper_ids}}

        response = self._collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where,
            include=["metadatas", "documents", "distances"],
        )

        ids = response.get("ids", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]
        documents = response.get("documents", [[]])[0]
        distances = response.get("distances", [[]])[0]

        items: list[dict[str, Any]] = []
        for idx, chunk_id in enumerate(ids):
            items.append(
                {
                    "chunk_id": chunk_id,
                    "metadata": metadatas[idx] if idx < len(metadatas) else {},
                    "document": documents[idx] if idx < len(documents) else "",
                    "distance": float(distances[idx]) if idx < len(distances) else 1.0,
                }
            )
        return items
