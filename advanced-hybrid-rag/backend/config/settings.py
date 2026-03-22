"""Application configuration for the advanced hybrid RAG backend."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal
from warnings import warn

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseModel):
	openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
	anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
	groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
	cohere_api_key: str | None = Field(default=None, alias="COHERE_API_KEY")
	ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
	default_llm_provider: Literal["openai", "anthropic", "groq", "ollama"] = Field(
		default="openai", alias="DEFAULT_LLM_PROVIDER"
	)
	default_llm_model: str = Field(default="gpt-4o", alias="DEFAULT_LLM_MODEL")
	fallback_llm_model: str = Field(default="gpt-4o-mini", alias="FALLBACK_LLM_MODEL")
	max_tokens: int = Field(default=2048, alias="MAX_TOKENS")
	temperature: float = Field(default=0.1, alias="TEMPERATURE")


class EmbeddingSettings(BaseModel):
	embedding_model: str = Field(default="BAAI/bge-large-en-v1.5", alias="EMBEDDING_MODEL")
	embedding_device: Literal["cpu", "cuda", "mps"] = Field(default="cpu", alias="EMBEDDING_DEVICE")
	reranker_model: str = Field(default="BAAI/bge-reranker-v2-m3", alias="RERANKER_MODEL")
	colbert_model: str = Field(default="colbert-ir/colbertv2.0", alias="COLBERT_MODEL")


class VectorStoreSettings(BaseModel):
	vector_store_type: Literal["chromadb", "pgvector", "faiss"] = Field(default="chromadb", alias="VECTOR_STORE_TYPE")
	chroma_host: str = Field(default="localhost", alias="CHROMA_HOST")
	chroma_port: int = Field(default=8000, alias="CHROMA_PORT")
	chroma_collection: str = Field(default="research_papers", alias="CHROMA_COLLECTION")
	pgvector_dsn: str = Field(default="postgresql://user:pass@localhost:5432/ragdb", alias="PGVECTOR_DSN")


class GraphSettings(BaseModel):
	neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
	neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
	neo4j_password: str = Field(default="password", alias="NEO4J_PASSWORD")


class CacheSettings(BaseModel):
	redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
	cache_ttl_seconds: int = Field(default=3600, alias="CACHE_TTL_SECONDS")
	semantic_cache_threshold: float = Field(default=0.92, alias="SEMANTIC_CACHE_THRESHOLD")


class RetrievalSettings(BaseModel):
	k_vector: int = Field(default=30, alias="K_VECTOR")
	k_bm25: int = Field(default=20, alias="K_BM25")
	k_graph: int = Field(default=10, alias="K_GRAPH")
	k_final: int = Field(default=5, alias="K_FINAL")
	k_rerank_candidates: int = Field(default=50, alias="K_RERANK_CANDIDATES")
	rrf_k_constant: int = Field(default=60, alias="RRF_K_CONSTANT")
	rerank_threshold: float = Field(default=0.3, alias="RERANK_THRESHOLD")
	min_relevance_score: float = Field(default=0.4, alias="MIN_RELEVANCE_SCORE")


class ChunkingSettings(BaseModel):
	chunk_strategy: Literal["recursive", "semantic", "section", "sliding"] = Field(
		default="semantic", alias="CHUNK_STRATEGY"
	)
	chunk_size: int = Field(default=512, alias="CHUNK_SIZE")
	chunk_overlap: int = Field(default=64, alias="CHUNK_OVERLAP")
	section_aware: bool = Field(default=True, alias="SECTION_AWARE")


class AdaptiveSettings(BaseModel):
	adaptive_enabled: bool = Field(default=True, alias="ADAPTIVE_ENABLED")
	max_corrective_retries: int = Field(default=3, alias="MAX_CORRECTIVE_RETRIES")
	min_diversity_score: float = Field(default=0.4, alias="MIN_DIVERSITY_SCORE")
	min_coverage_score: float = Field(default=0.5, alias="MIN_COVERAGE_SCORE")
	quality_threshold: float = Field(default=0.65, alias="QUALITY_THRESHOLD")


class ObservabilitySettings(BaseModel):
	langsmith_api_key: str | None = Field(default=None, alias="LANGSMITH_API_KEY")
	langsmith_project: str = Field(default="advanced-rag", alias="LANGSMITH_PROJECT")
	phoenix_collector_endpoint: str = Field(
		default="http://localhost:6006", alias="PHOENIX_COLLECTOR_ENDPOINT"
	)


class AuthSettings(BaseModel):
	secret_key: str = Field(default="your-secret-key-here", alias="SECRET_KEY")
	algorithm: str = Field(default="HS256", alias="ALGORITHM")
	access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
	api_key_header: str = Field(default="X-API-Key", alias="API_KEY_HEADER")


class ServerSettings(BaseModel):
	host: str = Field(default="0.0.0.0", alias="HOST")
	port: int = Field(default=8000, alias="PORT")
	workers: int = Field(default=4, alias="WORKERS")
	log_level: str = Field(default="info", alias="LOG_LEVEL")


class CelerySettings(BaseModel):
	celery_broker_url: str = Field(default="redis://localhost:6379/0", alias="CELERY_BROKER_URL")
	celery_result_backend: str = Field(default="redis://localhost:6379/1", alias="CELERY_RESULT_BACKEND")


class Settings(BaseSettings):
	"""Top-level settings object with grouped configuration sections."""

	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		case_sensitive=False,
		extra="ignore",
	)

	llm: LLMSettings = Field(default_factory=LLMSettings)
	embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
	vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
	graph: GraphSettings = Field(default_factory=GraphSettings)
	cache: CacheSettings = Field(default_factory=CacheSettings)
	retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)
	chunking: ChunkingSettings = Field(default_factory=ChunkingSettings)
	adaptive: AdaptiveSettings = Field(default_factory=AdaptiveSettings)
	observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
	auth: AuthSettings = Field(default_factory=AuthSettings)
	server: ServerSettings = Field(default_factory=ServerSettings)
	celery: CelerySettings = Field(default_factory=CelerySettings)

	@model_validator(mode="after")
	def warn_on_missing_provider_keys(self) -> "Settings":
		provider = self.llm.default_llm_provider
		if provider == "openai" and not self.llm.openai_api_key:
			warn("OPENAI_API_KEY is not set while DEFAULT_LLM_PROVIDER=openai.", stacklevel=2)
		if provider == "anthropic" and not self.llm.anthropic_api_key:
			warn("ANTHROPIC_API_KEY is not set while DEFAULT_LLM_PROVIDER=anthropic.", stacklevel=2)
		if provider == "groq" and not self.llm.groq_api_key:
			warn("GROQ_API_KEY is not set while DEFAULT_LLM_PROVIDER=groq.", stacklevel=2)
		return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	"""Return a cached settings instance."""
	return Settings()


__all__ = [
	"Settings",
	"LLMSettings",
	"EmbeddingSettings",
	"VectorStoreSettings",
	"GraphSettings",
	"CacheSettings",
	"RetrievalSettings",
	"ChunkingSettings",
	"AdaptiveSettings",
	"ObservabilitySettings",
	"AuthSettings",
	"ServerSettings",
	"CelerySettings",
	"get_settings",
]
