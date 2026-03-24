from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def _as_int(name: str, default: int) -> int:
    return int(_env(name, str(default)))


def _as_float(name: str, default: float) -> float:
    return float(_env(name, str(default)))


def _as_bool(name: str, default: bool) -> bool:
    raw = _env(name, "1" if default else "0").lower()
    return raw in {"1", "true", "yes", "on"}


def _as_csv(name: str, default: str = "") -> list[str]:
    raw = _env(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _resolve_path(raw: str, root_dir: Path) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return (root_dir / path).resolve()


@dataclass(slots=True)
class HybridRAGSettings:
    app_name: str
    app_env: str
    host: str
    port: int
    root_dir: Path
    data_dir: Path
    documents_dir: Path
    sqlite_path: Path
    chroma_path: Path
    chroma_collection: str
    embedding_model: str
    reranker_model: str
    llm_provider: str
    openai_api_key: str
    openai_base_url: str
    gemini_api_key: str
    gemini_base_url: str
    gemini_model: str
    llm_model: str
    openrouter_api_keys: list[str]
    openrouter_base_url: str
    openrouter_model: str
    mistral_api_key: str
    mistral_base_url: str
    mistral_model: str
    chunk_chars: int
    chunk_overlap: int
    base_k: int
    max_k: int
    rrf_k: int
    max_retries: int
    request_timeout_seconds: float
    enable_pdfplumber: bool
    enable_docling: bool
    enable_marker: bool
    use_citation_chain: bool
    citation_chain_max_papers: int
    arxiv_default_query: str
    arxiv_max_results: int
    arxiv_days_back: int
    arxiv_categories: list[str]
    arxiv_relevance_terms: list[str]

    @classmethod
    def from_env(cls) -> "HybridRAGSettings":
        root = Path(_env("APP_ROOT_DIR", ".")).expanduser().resolve()
        data_dir = _resolve_path(_env("RAG_DATA_DIR", "data"), root)
        return cls(
            app_name=_env("APP_NAME", "adaptive-hybrid-rag"),
            app_env=_env("APP_ENV", "development"),
            host=_env("APP_HOST", "0.0.0.0"),
            port=_as_int("APP_PORT", 8000),
            root_dir=root,
            data_dir=data_dir,
            documents_dir=_resolve_path(_env("RAG_DOCUMENTS_DIR", str(data_dir / "documents")), root),
            sqlite_path=_resolve_path(_env("RAG_SQLITE_PATH", str(data_dir / "rag_metadata.sqlite3")), root),
            chroma_path=_resolve_path(_env("RAG_CHROMA_PATH", str(data_dir / "chroma")), root),
            chroma_collection=_env("RAG_CHROMA_COLLECTION", "paper_chunks"),
            embedding_model=_env("RAG_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"),
            reranker_model=_env("RAG_RERANKER_MODEL", "BAAI/bge-reranker-base"),
            llm_provider=_env("LLM_PROVIDER", "openrouter"),
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            openai_base_url=_env("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            gemini_base_url=_env("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
            gemini_model=_env("GEMINI_MODEL", "gemini-2.5-flash"),
            llm_model=_env("OPENAI_RESPONSES_MODEL", "gpt-4o-mini"),
            openrouter_api_keys=_as_csv("OPENROUTER_API_KEYS", ""),
            openrouter_base_url=_env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            openrouter_model=_env("OPENROUTER_MODEL", "google/gemini-2.0-flash-001"),
            mistral_api_key=os.getenv("MISTRAL_API_KEY", "").strip(),
            mistral_base_url=_env("MISTRAL_BASE_URL", "https://api.mistral.ai/v1"),
            mistral_model=_env("MISTRAL_MODEL", "mistral-small-latest"),
            chunk_chars=_as_int("RAG_CHUNK_CHARS", 600),
            chunk_overlap=_as_int("RAG_CHUNK_OVERLAP", 80),
            base_k=_as_int("RAG_BASE_K", 12),
            max_k=_as_int("RAG_MAX_K", 30),
            rrf_k=_as_int("RAG_RRF_K", 60),
            max_retries=_as_int("RAG_MAX_RETRIES", 3),
            request_timeout_seconds=_as_float("REQUEST_TIMEOUT_SECONDS", 45.0),
            enable_pdfplumber=_as_bool("RAG_ENABLE_PDFPLUMBER", True),
            enable_docling=_as_bool("RAG_ENABLE_DOCLING", True),
            enable_marker=_as_bool("RAG_ENABLE_MARKER", True),
            use_citation_chain=_as_bool("RAG_USE_CITATION_CHAIN", True),
            citation_chain_max_papers=_as_int("RAG_CITATION_CHAIN_MAX_PAPERS", 3),
            arxiv_default_query=_env("ARXIV_DEFAULT_QUERY", "retrieval augmented generation"),
            arxiv_max_results=_as_int("ARXIV_MAX_RESULTS", 10),
            arxiv_days_back=_as_int("ARXIV_DAYS_BACK", 30),
            arxiv_categories=_as_csv("ARXIV_CATEGORIES", ""),
            arxiv_relevance_terms=_as_csv("ARXIV_RELEVANCE_TERMS", "retrieval,generation,rag,language model,agentic"),
        )

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.chroma_path.mkdir(parents=True, exist_ok=True)

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"
