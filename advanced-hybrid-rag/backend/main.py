"""FastAPI entry point for Advanced Hybrid RAG API."""

from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from .api.middleware import AuthMiddleware, RequestLoggingMiddleware
from .api.routes.analysis import router as analysis_router
from .api.routes.annotations import router as annotations_router
from .api.routes.debug import router as debug_router
from .api.routes.eval import router as eval_router
from .api.routes.feedback import router as feedback_router
from .api.routes.graph import router as graph_router
from .api.routes.health import router as health_router
from .api.routes.ingest import router as ingest_router
from .api.routes.literature import router as literature_router
from .api.routes.monitor import router as monitor_router
from .api.routes.papers import router as papers_router
from .api.routes.planning import router as planning_router
from .api.routes.query import router as query_router
from .api.websocket import router as websocket_router
from .adaptive.adaptive_controller import AdaptiveRetrievalController
from .adaptive.corrective_rag import CorrectiveRAG
from .adaptive.feedback_learner import FeedbackLearner
from .adaptive.quality_scorer import RetrievalQualityScorer

try:
    from .config.settings import get_settings
except Exception:  # pragma: no cover - optional dependency guard for lean test envs
    get_settings = None
from .ingestion.arxiv_monitor import ArxivMonitor
from .ingestion.embedder import BGEEmbedder
from .ingestion.pipeline import IngestionPipeline
from .ingestion.privacy_processor import PrivacyProcessor
from .reasoning.query_planning_agent import QueryPlanningAgent
from .reasoning.answer_generator import AnswerGenerator
from .reasoning.query_analyzer import QueryAnalyzer
from .reasoning.self_verifier import SelfVerifier
from .retrieval.bm25_retriever import BM25Retriever
from .retrieval.graph_retriever import GraphRetriever
from .retrieval.hybrid_engine import HybridRetrievalEngine, RetrievalFilters
from .retrieval.vector_retriever import VectorRetriever
from .storage.bm25_store import BM25Store
from .storage.cache_store import SemanticCache
from .storage.graph_store import Neo4jGraphStore
from .storage.annotation_store import AnnotationStore
from .storage.relational_store import RelationalStore
from .storage.vector_store import ChromaDBStore


def _configure_app_state(app: FastAPI) -> None:
    settings = None
    if get_settings is not None:
        try:
            settings = get_settings()
        except Exception:
            settings = None
    if settings is None:
        settings = SimpleNamespace(
            retrieval=SimpleNamespace(k_final=5),
            adaptive=SimpleNamespace(adaptive_enabled=True, max_corrective_retries=3, quality_threshold=0.65),
        )
    embedder = BGEEmbedder()
    vector_store = ChromaDBStore()
    bm25_store = BM25Store()
    graph_store = Neo4jGraphStore()
    relational_store = RelationalStore()
    cache_store = SemanticCache(redis_url="redis://localhost:6379")
    feedback_learner = FeedbackLearner()
    annotation_store = AnnotationStore()
    arxiv_monitor = ArxivMonitor()
    privacy_processor = PrivacyProcessor()
    query_planning_agent = QueryPlanningAgent()

    pipeline = IngestionPipeline(
        embedder=embedder,
        vector_store=vector_store,
        relational_store=relational_store,
        bm25_store=bm25_store,
        graph_store=graph_store,
        cache_store=cache_store,
        privacy_processor=privacy_processor,
    )

    retrieval_engine = HybridRetrievalEngine(
        embedder=embedder,
        vector_retriever=VectorRetriever(vector_store),
        bm25_retriever=BM25Retriever(bm25_store),
        graph_retriever=GraphRetriever(graph_store),
    )

    analyzer = QueryAnalyzer()
    answer_generator = AnswerGenerator()
    verifier = SelfVerifier()
    adaptive_controller = AdaptiveRetrievalController(settings=settings.adaptive)
    quality_scorer = RetrievalQualityScorer()

    async def _refine_retrieval(query: str, bad_chunks):
        _ = bad_chunks
        query_embedding = embedder.embed_query(query)
        refined = await retrieval_engine.retrieve(
            query=query,
            query_embedding=query_embedding,
            k_final=max(settings.retrieval.k_final, 8),
            filters=RetrievalFilters(),
            use_hyde=True,
            use_graph=True,
            use_colbert=True,
        )
        return refined.chunks

    async def _regenerate_answer(query: str, chunks):
        analysis = analyzer.analyze(query)
        regenerated = await answer_generator.generate(
            query=query,
            analysis=analysis,
            chunks=chunks,
            reasoning_trace=["corrective", "regenerate"],
        )
        return regenerated.model_dump()

    async def _optimize_retrieval(query: str, bad_chunks):
        _ = bad_chunks
        query_embedding = embedder.embed_query(query)
        baseline = await retrieval_engine.retrieve(
            query=query,
            query_embedding=query_embedding,
            k_final=max(settings.retrieval.k_final, 8),
            filters=RetrievalFilters(),
            use_hyde=False,
            use_graph=True,
            use_colbert=False,
        )
        quality = quality_scorer.score(query, query_embedding, baseline.chunks)
        return await adaptive_controller.optimize_retrieval(query=query, initial_results=baseline, quality=quality, attempt=1)

    async def _rerun_pipeline(query: str, params):
        query_embedding = embedder.embed_query(params.query)

        prev_k_vector = retrieval_engine.k_vector
        prev_k_bm25 = retrieval_engine.k_bm25
        prev_k_graph = retrieval_engine.k_graph
        prev_k_rerank = retrieval_engine.k_rerank_candidates
        prev_threshold = retrieval_engine.reranker.rerank_threshold
        try:
            retrieval_engine.k_vector = int(params.k_vector)
            retrieval_engine.k_bm25 = int(params.k_bm25)
            retrieval_engine.k_graph = int(params.k_graph)
            retrieval_engine.k_rerank_candidates = max(int(params.k_vector + params.k_bm25), prev_k_rerank)
            retrieval_engine.reranker.rerank_threshold = float(params.rerank_threshold)

            retrieval = await retrieval_engine.retrieve(
                query=params.query,
                query_embedding=query_embedding,
                k_final=max(settings.retrieval.k_final, 8),
                filters=RetrievalFilters(),
                use_hyde=bool(params.use_hyde),
                use_graph=bool(params.use_graph),
                use_colbert=bool(params.use_colbert),
            )
            analysis = analyzer.analyze(query)
            regenerated = await answer_generator.generate(
                query=query,
                analysis=analysis,
                chunks=retrieval.chunks,
                reasoning_trace=["corrective", "rerun"],
            )
            out = regenerated.model_dump()
            out["retrieval_quality"] = sum(retrieval.retrieval_scores.values()) / max(1, len(retrieval.retrieval_scores))
            return out
        finally:
            retrieval_engine.k_vector = prev_k_vector
            retrieval_engine.k_bm25 = prev_k_bm25
            retrieval_engine.k_graph = prev_k_graph
            retrieval_engine.k_rerank_candidates = prev_k_rerank
            retrieval_engine.reranker.rerank_threshold = prev_threshold

    corrective_rag = CorrectiveRAG(
        regenerate_answer=_regenerate_answer,
        refine_retrieval=_refine_retrieval,
        optimize_retrieval=_optimize_retrieval,
        rerun_pipeline=_rerun_pipeline,
    )

    app.state.embedder = embedder
    app.state.vector_store = vector_store
    app.state.bm25_store = bm25_store
    app.state.graph_store = graph_store
    app.state.relational_store = relational_store
    app.state.cache_store = cache_store
    app.state.pipeline = pipeline
    app.state.retrieval_engine = retrieval_engine
    app.state.settings = settings
    app.state.feedback_learner = feedback_learner
    app.state.annotation_store = annotation_store
    app.state.arxiv_monitor = arxiv_monitor
    app.state.privacy_processor = privacy_processor
    app.state.query_planning_agent = query_planning_agent
    app.state.services = {
        "embedder": embedder,
        "analyzer": analyzer,
        "answer_generator": answer_generator,
        "verifier": verifier,
        "quality_scorer": quality_scorer,
        "adaptive_controller": adaptive_controller,
        "corrective_rag": corrective_rag,
        "settings": settings,
        "retrieval_engine": retrieval_engine,
        "retrieval_filters_model": RetrievalFilters,
    }


@asynccontextmanager
async def _lifespan(app: FastAPI):
    _configure_app_state(app)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Advanced Hybrid RAG API", version="1.0.0", docs_url="/docs", redoc_url="/redoc", lifespan=_lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AuthMiddleware, enabled=False)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=500)

    app.include_router(health_router)
    app.include_router(ingest_router)
    app.include_router(query_router)
    app.include_router(papers_router)
    app.include_router(graph_router)
    app.include_router(eval_router)
    app.include_router(feedback_router)
    app.include_router(annotations_router)
    app.include_router(debug_router)
    app.include_router(analysis_router)
    app.include_router(literature_router)
    app.include_router(planning_router)
    app.include_router(monitor_router)
    app.include_router(websocket_router)

    @app.get("/api/stats")
    async def stats(request: Request):
        docs = request.app.state.relational_store.list_documents()
        return {
            "total_papers": len(docs),
            "cache_backend": "redis-or-memory",
            "model_usage_breakdown": {},
        }

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.exception_handler(404)
    async def not_found_handler(_: Request, __):
        return JSONResponse(status_code=404, content={"detail": "Route not found."})

    @app.exception_handler(500)
    async def server_error_handler(_: Request, __):
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})

    return app


app = create_app()
