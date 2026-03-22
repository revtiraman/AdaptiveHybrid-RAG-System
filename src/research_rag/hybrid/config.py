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
    chunk_chars: int
    chunk_overlap: int
    base_k: int
    max_k: int
    rrf_k: int
    max_retries: int
    request_timeout_seconds: float
    enable_pdfplumber: bool

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
            llm_provider=_env("LLM_PROVIDER", "openai"),
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            openai_base_url=_env("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            gemini_base_url=_env("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
            gemini_model=_env("GEMINI_MODEL", "gemini-2.0-flash"),
            llm_model=_env("OPENAI_RESPONSES_MODEL", "gpt-5-mini"),
            chunk_chars=_as_int("RAG_CHUNK_CHARS", 200),
            chunk_overlap=_as_int("RAG_CHUNK_OVERLAP", 40),
            base_k=_as_int("RAG_BASE_K", 10),
            max_k=_as_int("RAG_MAX_K", 30),
            rrf_k=_as_int("RAG_RRF_K", 60),
            max_retries=_as_int("RAG_MAX_RETRIES", 3),
            request_timeout_seconds=_as_float("REQUEST_TIMEOUT_SECONDS", 45.0),
            enable_pdfplumber=_as_bool("RAG_ENABLE_PDFPLUMBER", True),
        )

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.chroma_path.mkdir(parents=True, exist_ok=True)

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"
