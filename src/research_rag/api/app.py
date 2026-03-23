from __future__ import annotations

from typing import Any
from uuid import uuid4

try:
    from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "Running the API requires FastAPI and Pydantic. Install dependencies with `pip install -e .` first."
    ) from exc

from research_rag.bootstrap import ServiceContainer, build_container
from research_rag.hybrid.config import HybridRAGSettings
from research_rag.logging import bind_request_id, reset_request_id


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Natural-language question")
    paper_ids: list[str] | None = Field(default=None, description="Restrict retrieval to specific papers")
    filters: dict[str, Any] | None = Field(default=None, description="Optional metadata filters")


class ChunkSampleRequest(BaseModel):
    paper_id: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=50)


class PaperStructureRequest(BaseModel):
    paper_id: str = Field(..., min_length=1)


class ArxivSyncRequest(BaseModel):
    query: str | None = Field(default=None, min_length=1)
    max_results: int | None = Field(default=None, ge=1, le=100)
    days_back: int | None = Field(default=None, ge=1, le=365)
    categories: list[str] | None = None
    relevance_terms: list[str] | None = None
    dry_run: bool = False


class EvalRunRequest(BaseModel):
    dataset_path: str = Field(..., min_length=1)
    limit: int | None = Field(default=None, ge=1, le=1000)


def create_app() -> FastAPI:
    settings = HybridRAGSettings.from_env()
    container = build_container(settings)
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Adaptive Hybrid RAG for Scientific Paper Question Answering.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.container = container

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid4()))
        token = bind_request_id(request_id)
        try:
            response = await call_next(request)
        finally:
            reset_request_id(token)
        response.headers["x-request-id"] = request_id
        return response

    @app.get("/")
    async def root() -> dict[str, Any]:
        return {
            "service": settings.app_name,
            "architecture": "adaptive-hybrid-rag",
            "environment": settings.app_env,
            "docs": "/docs",
        }

    @app.get("/health/live")
    async def live() -> dict[str, Any]:
        return {"status": "ok", "service": settings.app_name}

    @app.get("/health/ready")
    async def ready(request: Request) -> dict[str, Any]:
        container = _container(request)
        stats = container.system.stats()
        return {
            "status": "ready",
            "papers_indexed": stats.papers,
            "chunks_indexed": stats.chunks,
            "embedding_provider": stats.embedding_provider,
            "reranker_provider": stats.reranker_provider,
            "sqlite_path": str(settings.sqlite_path),
            "chroma_path": str(settings.chroma_path),
        }

    @app.post("/upload")
    async def upload_paper(
        request: Request,
        file: UploadFile = File(...),
        title: str | None = Form(default=None),
        paper_id: str | None = Form(default=None),
    ) -> dict[str, Any]:
        container = _container(request)
        filename = file.filename or "uploaded-paper.pdf"
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

        temp_path = container.settings.documents_dir / f"tmp-{uuid4()}.pdf"
        content = await file.read()
        temp_path.write_bytes(content)

        try:
            report = container.system.ingest_pdf(pdf_path=str(temp_path), title=title or filename, paper_id=paper_id)
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        finally:
            if temp_path.exists():
                temp_path.unlink()

        return {"status": "ok", "paper": report}

    @app.post("/query")
    async def query(request: Request, payload: QueryRequest) -> dict[str, Any]:
        container = _container(request)
        try:
            result = container.system.query(
                question=payload.question,
                paper_ids=payload.paper_ids,
                filters=payload.filters,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return result.to_dict()

    @app.get("/papers")
    async def papers(request: Request) -> dict[str, Any]:
        container = _container(request)
        return {"papers": container.system.list_papers()}

    @app.get("/stats")
    async def stats(request: Request) -> dict[str, Any]:
        container = _container(request)
        system_stats = container.system.stats()
        return {
            "papers": system_stats.papers,
            "chunks": system_stats.chunks,
            "embedding_provider": system_stats.embedding_provider,
            "reranker_provider": system_stats.reranker_provider,
            "llm_provider": system_stats.llm_provider,
            "targets": {
                "simple_query_seconds": "3-8",
                "complex_query_seconds": "10-20",
                "hallucination_policy": "self-verified with retries",
            },
        }

    @app.post("/debug/chunk-sample")
    async def debug_chunk_sample(request: Request, payload: ChunkSampleRequest) -> dict[str, Any]:
        container = _container(request)
        paper = container.system.metadata_store.get_paper(payload.paper_id)
        if paper is None:
            raise HTTPException(status_code=404, detail=f"Unknown paper_id: {payload.paper_id}")

        samples = container.system.metadata_store.fetch_chunk_samples(payload.paper_id, limit=payload.limit)
        return {
            "paper_id": payload.paper_id,
            "title": paper.title,
            "sample_count": len(samples),
            "chunks": samples,
        }

    @app.post("/debug/paper-structure")
    async def debug_paper_structure(request: Request, payload: PaperStructureRequest) -> dict[str, Any]:
        container = _container(request)
        paper = container.system.metadata_store.get_paper(payload.paper_id)
        if paper is None:
            raise HTTPException(status_code=404, detail=f"Unknown paper_id: {payload.paper_id}")

        structure = container.system.metadata_store.fetch_paper_structure(payload.paper_id)
        structure["title"] = paper.title
        return structure

    @app.post("/pipeline/arxiv/sync")
    async def arxiv_sync(request: Request, payload: ArxivSyncRequest) -> dict[str, Any]:
        container = _container(request)
        return container.system.arxiv_sync(
            query=payload.query or container.settings.arxiv_default_query,
            max_results=payload.max_results or container.settings.arxiv_max_results,
            days_back=payload.days_back or container.settings.arxiv_days_back,
            categories=payload.categories or container.settings.arxiv_categories,
            relevance_terms=payload.relevance_terms or container.settings.arxiv_relevance_terms,
            dry_run=payload.dry_run,
        )

    @app.post("/eval/run")
    async def eval_run(request: Request, payload: EvalRunRequest) -> dict[str, Any]:
        container = _container(request)
        try:
            return container.system.evaluate(dataset_path=payload.dataset_path, limit=payload.limit)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return app


def _container(request: Request) -> ServiceContainer:
    return request.app.state.container
