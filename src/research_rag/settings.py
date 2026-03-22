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


def _as_api_keys(name: str) -> dict[str, str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return {}

    api_keys: dict[str, str] = {}
    for item in raw.split(","):
        token = item.strip()
        if not token:
            continue

        if ":" in token:
            tenant_id, key = token.split(":", 1)
            tenant = tenant_id.strip()
            api_key = key.strip()
        else:
            tenant = "default"
            api_key = token

        if not tenant:
            raise ValueError(f"{name} contains an entry with an empty tenant id")
        if not api_key:
            raise ValueError(f"{name} contains an empty API key")
        api_keys[api_key] = tenant

    return api_keys


def _resolve_path(raw: str, root: Path) -> Path:
    path = Path(raw).expanduser()
    return path if path.is_absolute() else (root / path).resolve()


@dataclass(slots=True)
class Settings:
    app_name: str
    app_env: str
    log_level: str
    host: str
    port: int
    root_dir: Path
    storage_path: Path
    documents_dir: Path
    default_top_k: int
    chunk_size: int
    chunk_overlap: int
    embedding_provider: str
    hash_embedding_dimension: int
    generation_provider: str
    openai_api_key: str
    openai_base_url: str
    openai_embedding_model: str
    openai_responses_model: str
    request_timeout_seconds: float
    api_keys: dict[str, str]

    @classmethod
    def from_env(cls) -> "Settings":
        root_dir = Path(_env("APP_ROOT_DIR", ".")).expanduser().resolve()
        settings = cls(
            app_name=_env("APP_NAME", "research-rag-service"),
            app_env=_env("APP_ENV", "development"),
            log_level=_env("LOG_LEVEL", "INFO"),
            host=_env("APP_HOST", "0.0.0.0"),
            port=_as_int("APP_PORT", 8000),
            root_dir=root_dir,
            storage_path=_resolve_path(_env("RAG_STORAGE_PATH", "data/rag.sqlite3"), root_dir),
            documents_dir=_resolve_path(_env("RAG_DOCUMENTS_DIR", "data/documents"), root_dir),
            default_top_k=_as_int("RAG_TOP_K", 5),
            chunk_size=_as_int("RAG_CHUNK_SIZE", 220),
            chunk_overlap=_as_int("RAG_CHUNK_OVERLAP", 40),
            embedding_provider=_env("EMBEDDING_PROVIDER", "hash"),
            hash_embedding_dimension=_as_int("HASH_EMBEDDING_DIMENSION", 384),
            generation_provider=_env("GENERATION_PROVIDER", "extractive"),
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            openai_base_url=_env("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            openai_embedding_model=_env("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            openai_responses_model=_env("OPENAI_RESPONSES_MODEL", "gpt-5-mini"),
            request_timeout_seconds=_as_float("REQUEST_TIMEOUT_SECONDS", 45.0),
            api_keys=_as_api_keys("API_KEYS"),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("RAG_CHUNK_SIZE must be positive")
        if self.chunk_overlap < 0 or self.chunk_overlap >= self.chunk_size:
            raise ValueError("RAG_CHUNK_OVERLAP must be between 0 and chunk size - 1")
        if self.default_top_k <= 0:
            raise ValueError("RAG_TOP_K must be positive")
        if self.hash_embedding_dimension <= 0:
            raise ValueError("HASH_EMBEDDING_DIMENSION must be positive")

    def ensure_directories(self) -> None:
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def api_auth_enabled(self) -> bool:
        return bool(self.api_keys)
