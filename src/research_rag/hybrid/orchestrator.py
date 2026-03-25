from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from research_rag.hybrid.config import HybridRAGSettings
from research_rag.hybrid.domain import QueryResult
from research_rag.hybrid.engines.adaptive_engine import AdaptiveCorrectiveEngine
from research_rag.hybrid.engines.arxiv_pipeline import ArxivAutoPipeline
from research_rag.hybrid.engines.chunker import SectionAwareChunker
from research_rag.hybrid.engines.citation_chain_retriever import CitationChainRetriever
from research_rag.hybrid.engines.context_enricher import ContextEnricher
from research_rag.hybrid.engines.embedding import BGEEmbedder, CrossEncoderReranker
from research_rag.hybrid.engines.eval_harness import EvaluationHarness
from research_rag.hybrid.engines.ingestion_engine import IngestionEngine
from research_rag.hybrid.engines.llm import LLMClient
from research_rag.hybrid.engines.pdf_parser import PDFParser
from research_rag.hybrid.engines.reasoning_engine import ReasoningEngine
from research_rag.hybrid.engines.retrieval_engine import HybridRetrievalEngine
from research_rag.hybrid.storage.chroma_store import VectorStore
from research_rag.hybrid.storage.sqlite_store import MetadataStore


@dataclass(slots=True)
class HybridSystemStats:
    papers: int
    chunks: int
    embedding_provider: str
    reranker_provider: str
    llm_provider: str


class HybridRAGSystem:
    def __init__(self, settings: HybridRAGSettings) -> None:
        self.settings = settings
        settings.ensure_directories()

        self.metadata_store = MetadataStore(settings.sqlite_path)
        self.metadata_store.initialize()

        self.vector_store = VectorStore(settings)
        self.vector_store.initialize()

        self.embedder = BGEEmbedder(settings.embedding_model)
        self.reranker = CrossEncoderReranker(settings.reranker_model)

        llm_client = None
        if settings.llm_provider == "mistral" and settings.mistral_api_key:
            llm_client = LLMClient(
                provider="mistral",
                model=settings.mistral_model,
                api_key=settings.mistral_api_key,
                base_url=settings.mistral_base_url,
                timeout_seconds=settings.request_timeout_seconds,
            )
        elif settings.llm_provider == "openrouter" and settings.openrouter_api_keys:
            llm_client = LLMClient(
                provider="openrouter",
                model=settings.openrouter_model,
                api_key=settings.openrouter_api_keys[0],
                base_url=settings.openrouter_base_url,
                timeout_seconds=settings.request_timeout_seconds,
                extra_api_keys=settings.openrouter_api_keys[1:],
            )
        elif settings.llm_provider == "openai" and settings.openai_api_key:
            llm_client = LLMClient(
                provider="openai",
                model=settings.llm_model,
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                timeout_seconds=settings.request_timeout_seconds,
            )
        elif settings.llm_provider == "gemini" and settings.gemini_api_key:
            llm_client = LLMClient(
                provider="gemini",
                model=settings.gemini_model,
                api_key=settings.gemini_api_key,
                base_url=settings.gemini_base_url,
                timeout_seconds=settings.request_timeout_seconds,
            )

        self.ingestion = IngestionEngine(
            settings=settings,
            parser=PDFParser(
                enable_pdfplumber=settings.enable_pdfplumber,
                enable_docling=settings.enable_docling,
                enable_marker=settings.enable_marker,
            ),
            chunker=SectionAwareChunker(chunk_chars=settings.chunk_chars, overlap=settings.chunk_overlap),
            embedder=self.embedder,
            vector_store=self.vector_store,
            metadata_store=self.metadata_store,
        )
        self.retrieval = HybridRetrievalEngine(
            metadata_store=self.metadata_store,
            vector_store=self.vector_store,
            embedder=self.embedder,
            reranker=self.reranker,
            rrf_k=settings.rrf_k,
        )
        self.reasoning = ReasoningEngine(llm_client=llm_client)
        self._active_llm_provider = llm_client.provider if llm_client else "none"
        self.context_enricher = ContextEnricher()
        self.citation_chain = CitationChainRetriever(self.metadata_store)
        self.adaptive = AdaptiveCorrectiveEngine(
            base_k=settings.base_k,
            max_k=settings.max_k,
            max_retries=settings.max_retries,
        )
        self.arxiv_pipeline = ArxivAutoPipeline(system=self, documents_dir=settings.documents_dir)
        self.evaluation_harness = EvaluationHarness(system=self)

    def ingest_pdf(self, pdf_path: str, title: str | None = None, paper_id: str | None = None) -> dict[str, object]:
        return self.ingestion.ingest_pdf(pdf_path=pdf_path, title=title, paper_id=paper_id).to_dict()

    def query(self, question: str, paper_ids: list[str] | None = None, filters: dict[str, object] | None = None) -> QueryResult:
        started = perf_counter()
        plan = self.reasoning.classify_query(question)

        # HyDE: generate a hypothetical answer passage for better dense retrieval.
        # Falls back to original question if LLM unavailable.
        hyde_query = self.reasoning.generate_hyde_query(question)

        retries = 0
        final_candidates = []
        final_answer = ""
        final_claims = []
        verification = None
        quality = 0.0
        citation_augmented_count = 0

        while True:
            k = self.adaptive.choose_k(quality=quality, retry_count=retries, query_type=plan.query_type)
            candidates = self.retrieval.retrieve(
                query=question,
                top_k=k,
                paper_ids=paper_ids,
                filters=filters,
                per_section_cap=3,
                dense_query=hyde_query,
            )

            if self.settings.use_citation_chain and plan.query_type == "multi_hop":
                citation_candidates = self.citation_chain.retrieve_with_citations(
                    query=question,
                    primary_candidates=candidates,
                    max_papers=self.settings.citation_chain_max_papers,
                    top_chunks_per_paper=2,
                )
                if citation_candidates:
                    citation_augmented_count = len(citation_candidates)
                    candidates = sorted(candidates + citation_candidates, key=lambda item: item.rrf_score, reverse=True)
                    candidates = candidates[: max(k, len(candidates))]

            corpus_chunks = self.metadata_store.fetch_chunks(paper_ids=paper_ids)
            candidates = self.context_enricher.enrich(candidates, corpus_chunks=corpus_chunks, window=1)
            quality = self.adaptive.retrieval_quality(candidates)

            # Retry retrieval first when context quality is too low.
            if quality < self.adaptive.min_quality_threshold and retries < self.adaptive.max_retries:
                retries += 1
                continue

            answer, claims = self.reasoning.generate_answer(question=question, plan=plan, contexts=candidates)
            verification = self.adaptive.verify_answer(answer, [item.chunk.text for item in candidates])

            final_candidates = candidates
            final_answer = answer
            final_claims = claims

            llm_error = self.reasoning.last_llm_error or ""
            if llm_error:
                _permanent_error_tokens = [
                    "quota", "resource_exhausted", "429",
                    "model_not_found", "model not found", "does not exist",
                    "invalid model", "no such model", "decommissioned",
                    "unauthorized", "401", "403", "invalid_api_key",
                ]
                if any(token in llm_error.lower() for token in _permanent_error_tokens):
                    # Do not waste retries on permanent provider errors.
                    break

            llm_available = self._active_llm_provider != "none" and not self.reasoning.last_llm_error
            if not self.adaptive.should_retry(verification=verification, quality=quality, retries=retries, llm_available=llm_available):
                break
            retries += 1

        citations = []
        seen = set()
        for claim in final_claims:
            for citation in claim.citations:
                key = (citation.get("paper_id"), citation.get("chunk_id"), citation.get("page_number"))
                if key in seen:
                    continue
                seen.add(key)
                citations.append(citation)

        latency_ms = int((perf_counter() - started) * 1000)
        diagnostic = {
            "retrieved_chunks": [
                {
                    "chunk_id": c.chunk.chunk_id,
                    "paper_id": c.chunk.paper_id,
                    "page_number": c.chunk.page_number,
                    "section": c.chunk.section,
                    "rrf_score": round(c.rrf_score, 4),
                    "rerank_score": round(c.rerank_score, 4),
                }
                for c in final_candidates[:20]
            ],
            "verification": {
                "supported": verification.supported if verification else False,
                "confidence": verification.confidence if verification else 0.0,
                "unsupported_claims": verification.unsupported_claims if verification else [],
                "issues": verification.issues if verification else [],
                "stage_scores": verification.stage_scores if verification else {},
            },
            "llm_error": self.reasoning.last_llm_error,
            "k_final": len(final_candidates),
            "citation_augmented_count": citation_augmented_count,
        }

        return QueryResult(
            question=question,
            query_type=plan.query_type,
            hops=plan.hops,
            answer=final_answer,
            claims=final_claims,
            citations=citations,
            retrieval_quality=quality,
            retries=retries,
            latency_ms=latency_ms,
            diagnostic=diagnostic,
        )

    def list_papers(self) -> list[dict[str, object]]:
        return [
            {
                "paper_id": p.paper_id,
                "title": p.title,
                "source_path": p.source_path,
                "page_count": p.page_count,
                "chunk_count": p.chunk_count,
                "updated_at": p.updated_at,
            }
            for p in self.metadata_store.list_papers()
        ]

    def stats(self) -> HybridSystemStats:
        papers = len(self.metadata_store.list_papers())
        chunks = self.metadata_store.count_chunks()
        return HybridSystemStats(
            papers=papers,
            chunks=chunks,
            embedding_provider=self.embedder.provider_name,
            reranker_provider=self.reranker.provider_name,
            llm_provider=self._active_llm_provider,
        )

    def arxiv_sync(
        self,
        query: str,
        max_results: int,
        days_back: int,
        categories: list[str] | None = None,
        relevance_terms: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict[str, object]:
        return self.arxiv_pipeline.run(
            query=query,
            max_results=max_results,
            days_back=days_back,
            categories=categories,
            relevance_terms=relevance_terms,
            dry_run=dry_run,
        )

    def evaluate(self, dataset_path: str, limit: int | None = None) -> dict[str, object]:
        return self.evaluation_harness.run(dataset_path=dataset_path, limit=limit)
