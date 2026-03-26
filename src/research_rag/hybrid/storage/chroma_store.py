from __future__ import annotations

# pyright: reportMissingImports=false

from typing import Any

from research_rag.hybrid.config import HybridRAGSettings
from research_rag.hybrid.domain import ClaimRecord, SectionChunk


class VectorStore:
    def __init__(self, settings: HybridRAGSettings) -> None:
        self.settings = settings
        self._client = None
        self._collection = None
        self._claims_collection = None

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
        self._claims_collection = self._client.get_or_create_collection(name=f"{self.settings.chroma_collection}_claims")

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

    def upsert_claims(self, claims: list[ClaimRecord], embeddings: list[list[float]]) -> None:
        if not claims:
            return
        if self._claims_collection is None:
            raise RuntimeError("Vector store not initialized")

        self._claims_collection.upsert(
            ids=[c.claim_id for c in claims],
            embeddings=embeddings,
            documents=[c.claim for c in claims],
            metadatas=[
                {
                    "paper_id": c.paper_id,
                    "chunk_id": c.chunk_id,
                    "claim_type": c.claim_type,
                    "section": c.section,
                    "page_number": c.page_number,
                    "confidence": c.confidence,
                }
                for c in claims
            ],
        )

    def query_claims(self, query_vector: list[float], top_k: int, paper_ids: list[str] | None = None) -> list[dict[str, Any]]:
        if self._claims_collection is None:
            raise RuntimeError("Vector store not initialized")

        where = None
        if paper_ids:
            where = {"paper_id": {"$in": paper_ids}}

        response = self._claims_collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where,
            include=["metadatas", "documents", "distances"],
        )

    def delete_by_paper(self, paper_id: str) -> None:
        """Remove all chunk and claim vectors for a given paper from ChromaDB."""
        if self._collection is not None:
            try:
                self._collection.delete(where={"paper_id": paper_id})
            except Exception:
                pass
        if self._claims_collection is not None:
            try:
                self._claims_collection.delete(where={"paper_id": paper_id})
            except Exception:
                pass

        ids = response.get("ids", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]
        documents = response.get("documents", [[]])[0]
        distances = response.get("distances", [[]])[0]

        items: list[dict[str, Any]] = []
        for idx, claim_id in enumerate(ids):
            md = metadatas[idx] if idx < len(metadatas) else {}
            items.append(
                {
                    "claim_id": claim_id,
                    "chunk_id": md.get("chunk_id"),
                    "paper_id": md.get("paper_id"),
                    "claim_type": md.get("claim_type"),
                    "section": md.get("section"),
                    "page_number": md.get("page_number"),
                    "confidence": md.get("confidence"),
                    "claim": documents[idx] if idx < len(documents) else "",
                    "distance": float(distances[idx]) if idx < len(distances) else 1.0,
                }
            )
        return items
