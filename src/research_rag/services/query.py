from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class QueryResponse:
    question: str
    answer: str
    citations: list[dict[str, object]]
    retrieved_chunks: list[dict[str, object]]
    generator: str

    def to_dict(self) -> dict[str, object]:
        return {
            "question": self.question,
            "answer": self.answer,
            "citations": self.citations,
            "retrieved_chunks": self.retrieved_chunks,
            "generator": self.generator,
        }


class RagQueryService:
    def __init__(self, default_top_k: int, embedding_provider, store, generator) -> None:
        self.default_top_k = default_top_k
        self.embedding_provider = embedding_provider
        self.store = store
        self.generator = generator

    def query(
        self,
        question: str,
        top_k: int | None = None,
        document_id: str | None = None,
        document_ids: list[str] | None = None,
    ) -> QueryResponse:
        cleaned_question = question.strip()
        if not cleaned_question:
            raise ValueError("Question must not be empty")

        query_embedding = self.embedding_provider.embed_texts([cleaned_question])[0]
        effective_top_k = top_k or self.default_top_k
        results = self.store.search(
            query_embedding=query_embedding,
            top_k=effective_top_k,
            document_id=document_id,
            document_ids=document_ids,
        )
        answer = self.generator.generate(cleaned_question, results)

        retrieved_chunks = [
            {
                "document_id": result.chunk.document_id,
                "chunk_id": result.chunk.chunk_id,
                "page_number": result.chunk.page_number,
                "score": round(result.score, 4),
                "text_preview": result.chunk.text[:320],
            }
            for result in results
        ]
        return QueryResponse(
            question=cleaned_question,
            answer=answer.answer,
            citations=answer.citations,
            retrieved_chunks=retrieved_chunks,
            generator=answer.provider,
        )
