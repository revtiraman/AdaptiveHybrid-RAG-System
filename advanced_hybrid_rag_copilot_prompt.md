# ============================================================
# GITHUB COPILOT — ADVANCED HYBRID RAG SYSTEM
# End-to-End Build Prompt (Ultra-Detailed)
# ============================================================
#
# HOW TO USE THIS PROMPT
# ─────────────────────
# 1. Open GitHub Copilot Chat in VS Code (Ctrl+Shift+I)
# 2. Select "Agent" mode (not "Ask" or "Edit")
# 3. Paste this entire file as your first message.
# 4. Then work section by section, pasting each PHASE block
#    in separate follow-up messages.
# 5. After each phase Copilot generates code, review it,
#    then proceed to the next phase.
#
# PROJECT OVERVIEW
# ─────────────────────────────────────────────────────────────
# Build a production-grade, research-focused Adaptive Hybrid
# Retrieval-Augmented Generation (RAG) system that goes far
# beyond a basic RAG demo. This system must handle:
#   - Multi-source document ingestion (PDF, web, CSV, JSON)
#   - Hybrid retrieval (dense vector + BM25 + knowledge graph)
#   - Cross-encoder reranking + HyDE + ColBERT
#   - Multi-hop reasoning with Chain-of-Thought decomposition
#   - Corrective RAG (CRAG) with self-verification loops
#   - Adaptive quality scoring & dynamic parameter tuning
#   - Multi-LLM routing (OpenAI, Anthropic, Groq, Ollama)
#   - Semantic caching with Redis
#   - Knowledge graph integration (Neo4j)
#   - Full observability (LangSmith / Arize Phoenix tracing)
#   - REST API + WebSocket streaming (FastAPI)
#   - React frontend + Streamlit demo interface
#   - Evaluation framework (RAGAS metrics)
#   - Docker + Docker Compose deployment
#
# ============================================================

# ============================================================
# PHASE 0 — PROJECT SCAFFOLD & MONOREPO STRUCTURE
# ============================================================

"""
Create the following complete directory & file scaffold for the
project. Use Python 3.11+. Use uv for dependency management
where possible; fall back to pip + requirements.txt otherwise.

PROJECT ROOT: advanced-hybrid-rag/

advanced-hybrid-rag/
├── .env.example                  # All env vars with descriptions
├── .gitignore
├── docker-compose.yml            # Full stack orchestration
├── docker-compose.dev.yml        # Dev overrides (hot-reload)
├── Makefile                      # Convenience commands
├── README.md                     # Full setup & usage guide
├── pyproject.toml                # Python project config
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                   # FastAPI app entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py           # Pydantic BaseSettings
│   │   └── prompts.py            # All LLM prompt templates
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── pdf_processor.py      # pdfplumber + pypdf + pymupdf
│   │   ├── web_scraper.py        # playwright + trafilatura
│   │   ├── csv_json_loader.py    # structured data ingestion
│   │   ├── chunker.py            # multiple chunking strategies
│   │   ├── embedder.py           # BGE + OpenAI + Cohere embedders
│   │   ├── metadata_extractor.py # title, authors, DOI, section
│   │   └── pipeline.py           # orchestrates the full flow
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── vector_store.py       # ChromaDB + pgvector abstraction
│   │   ├── bm25_store.py         # rank-bm25 index management
│   │   ├── graph_store.py        # Neo4j knowledge graph
│   │   ├── relational_store.py   # SQLAlchemy + SQLite/PostgreSQL
│   │   └── cache_store.py        # Redis semantic cache
│   │
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── vector_retriever.py   # Dense HNSW search
│   │   ├── bm25_retriever.py     # Sparse keyword search
│   │   ├── graph_retriever.py    # Neo4j Cypher-based traversal
│   │   ├── hyde_retriever.py     # Hypothetical Document Embedding
│   │   ├── colbert_retriever.py  # Late-interaction multi-vector
│   │   ├── fusion.py             # RRF + weighted combination
│   │   ├── reranker.py           # BGE-reranker + cross-encoder
│   │   └── hybrid_engine.py      # Orchestrates all retrievers
│   │
│   ├── adaptive/
│   │   ├── __init__.py
│   │   ├── quality_scorer.py     # Relevance, diversity, coverage
│   │   ├── adaptive_controller.py# Adjusts k, strategy, weights
│   │   ├── query_reformulator.py # HyDE, step-back, expansion
│   │   └── corrective_rag.py     # CRAG loop implementation
│   │
│   ├── reasoning/
│   │   ├── __init__.py
│   │   ├── query_analyzer.py     # Intent + complexity detection
│   │   ├── decomposer.py         # Multi-hop sub-question gen
│   │   ├── chain_of_thought.py   # CoT prompting + tree-of-thought
│   │   ├── self_verifier.py      # Grounding + hallucination check
│   │   ├── llm_router.py         # Multi-provider LLM routing
│   │   ├── answer_generator.py   # Final answer synthesis
│   │   ├── citation_generator.py # Page-level citation tracking
│   │   └── structured_output.py  # Pydantic response models
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── ragas_evaluator.py    # RAGAS faithfulness, relevancy
│   │   ├── retrieval_metrics.py  # Precision, Recall, MRR, NDCG
│   │   ├── latency_profiler.py   # End-to-end timing
│   │   └── benchmark_runner.py   # Automated test suite
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── ingest.py         # POST /api/ingest
│   │   │   ├── query.py          # POST /api/query (+ streaming)
│   │   │   ├── papers.py         # GET/DELETE /api/papers
│   │   │   ├── graph.py          # GET /api/graph
│   │   │   ├── eval.py           # POST /api/evaluate
│   │   │   └── health.py         # GET /api/health
│   │   ├── middleware.py         # CORS, rate limit, auth
│   │   ├── auth.py               # JWT + API key auth
│   │   └── websocket.py          # Streaming response handler
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py             # Structured logging
│       ├── tracing.py            # LangSmith / Arize Phoenix
│       └── helpers.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── components/
│       │   ├── ChatInterface.tsx      # Main chat panel
│       │   ├── DocumentUpload.tsx     # Drag-drop upload
│       │   ├── CitationViewer.tsx     # Expandable source panel
│       │   ├── GraphViewer.tsx        # D3 knowledge graph viz
│       │   ├── EvalDashboard.tsx      # Metrics visualization
│       │   ├── ReasoningTrace.tsx     # Multi-hop steps viewer
│       │   └── SettingsPanel.tsx      # Model / retrieval config
│       ├── hooks/
│       │   ├── useQuery.ts
│       │   ├── useUpload.ts
│       │   └── useStream.ts           # SSE streaming hook
│       ├── store/
│       │   └── ragStore.ts            # Zustand global state
│       └── types/
│           └── index.ts
│
├── streamlit_demo/
│   ├── app.py                    # Full Streamlit demo app
│   └── requirements.txt
│
├── notebooks/
│   ├── 01_ingestion_demo.ipynb
│   ├── 02_retrieval_benchmark.ipynb
│   ├── 03_ragas_evaluation.ipynb
│   └── 04_graph_exploration.ipynb
│
├── tests/
│   ├── unit/
│   │   ├── test_chunker.py
│   │   ├── test_retrieval.py
│   │   ├── test_fusion.py
│   │   └── test_verifier.py
│   ├── integration/
│   │   ├── test_pipeline.py
│   │   └── test_api.py
│   └── e2e/
│       └── test_full_query.py
│
└── data/
    ├── sample_papers/            # Included test PDFs
    └── eval_datasets/            # QASPER, NarrativeQA, etc.
"""

# ============================================================
# PHASE 1 — ENVIRONMENT, CONFIG & DEPENDENCIES
# ============================================================

"""
1A. Create pyproject.toml with ALL dependencies:

[project]
name = "advanced-hybrid-rag"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
  # Core framework
  "fastapi>=0.111",
  "uvicorn[standard]>=0.29",
  "pydantic>=2.7",
  "pydantic-settings>=2.3",
  
  # LLM providers
  "openai>=1.30",
  "anthropic>=0.28",
  "groq>=0.9",
  "litellm>=1.40",          # unified LLM interface
  "ollama>=0.2",             # local models
  
  # Embeddings & retrieval
  "sentence-transformers>=3.0",
  "transformers>=4.41",
  "torch>=2.3",
  "chromadb>=0.5",
  "pgvector>=0.3",           # PostgreSQL vector extension
  "rank-bm25>=0.2",
  "faiss-cpu>=1.8",          # alternative to HNSW
  
  # Knowledge graph
  "neo4j>=5.20",
  "networkx>=3.3",
  
  # Document processing
  "pdfplumber>=0.11",
  "pypdf>=4.2",
  "pymupdf>=1.24",           # fitz - best for complex PDFs
  "python-docx>=1.1",
  "trafilatura>=1.9",        # web content extraction
  "playwright>=1.44",        # JS-rendered web pages
  "unstructured[pdf,docx]>=0.14",  # Unstructured.io
  
  # Semantic cache
  "redis>=5.0",
  "redisvl>=0.1",            # Redis vector library
  
  # Storage
  "sqlalchemy>=2.0",
  "alembic>=1.13",
  "aiosqlite>=0.20",
  
  # Data processing
  "numpy>=1.26",
  "pandas>=2.2",
  "scipy>=1.13",
  
  # Evaluation
  "ragas>=0.1.9",
  "deepeval>=0.21",
  
  # Observability
  "langsmith>=0.1.77",
  "opentelemetry-sdk>=1.24",
  "arize-phoenix>=4.0",
  
  # Auth & middleware
  "python-jose[cryptography]>=3.3",
  "passlib[bcrypt]>=1.7",
  "slowapi>=0.1",            # rate limiting
  
  # Utilities
  "httpx>=0.27",
  "tenacity>=8.3",           # retry logic
  "python-multipart>=0.0.9",
  "pyyaml>=6.0",
  "rich>=13.7",
  "loguru>=0.7",
  "celery[redis]>=5.4",      # async task queue
]

1B. Create .env.example — include ALL of these variables:

# ── LLM Providers ──────────────────────────────────────────
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk-...
COHERE_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434

# ── Default LLM Settings ───────────────────────────────────
DEFAULT_LLM_PROVIDER=openai           # openai|anthropic|groq|ollama
DEFAULT_LLM_MODEL=gpt-4o
FALLBACK_LLM_MODEL=gpt-4o-mini
MAX_TOKENS=2048
TEMPERATURE=0.1

# ── Embedding Settings ─────────────────────────────────────
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
EMBEDDING_DEVICE=cpu                   # cpu|cuda|mps
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
COLBERT_MODEL=colbert-ir/colbertv2.0

# ── Vector Store ───────────────────────────────────────────
VECTOR_STORE_TYPE=chromadb             # chromadb|pgvector|faiss
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION=research_papers
PGVECTOR_DSN=postgresql://user:pass@localhost:5432/ragdb

# ── Knowledge Graph ────────────────────────────────────────
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# ── Cache ──────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379
CACHE_TTL_SECONDS=3600
SEMANTIC_CACHE_THRESHOLD=0.92         # cosine sim for cache hit

# ── Retrieval Parameters ───────────────────────────────────
K_VECTOR=30
K_BM25=20
K_GRAPH=10
K_FINAL=5
K_RERANK_CANDIDATES=50
RRF_K_CONSTANT=60
RERANK_THRESHOLD=0.3
MIN_RELEVANCE_SCORE=0.4

# ── Chunking ───────────────────────────────────────────────
CHUNK_STRATEGY=semantic               # recursive|semantic|section|sliding
CHUNK_SIZE=512
CHUNK_OVERLAP=64
SECTION_AWARE=true

# ── Adaptive Controller ────────────────────────────────────
ADAPTIVE_ENABLED=true
MAX_CORRECTIVE_RETRIES=3
MIN_DIVERSITY_SCORE=0.4
MIN_COVERAGE_SCORE=0.5
QUALITY_THRESHOLD=0.65

# ── Observability ──────────────────────────────────────────
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=advanced-rag
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006

# ── Auth ───────────────────────────────────────────────────
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
API_KEY_HEADER=X-API-Key

# ── Server ─────────────────────────────────────────────────
HOST=0.0.0.0
PORT=8000
WORKERS=4
LOG_LEVEL=info

# ── Celery Task Queue ──────────────────────────────────────
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

1C. Create config/settings.py using Pydantic BaseSettings.
    Group settings into nested classes (LLMSettings,
    RetrievalSettings, ChunkingSettings, etc.).
    Add validator methods that warn on missing API keys.
"""

# ============================================================
# PHASE 2 — DOCUMENT INGESTION PIPELINE
# ============================================================

"""
Build the complete ingestion system. Each component below
must be implemented as a class with clear interfaces.

2A. PDF Processor (ingestion/pdf_processor.py)
─────────────────────────────────────────────
Implement class PDFProcessor:

  def process(self, file_path: str | Path) -> ProcessedDocument:
    """
    Returns: ProcessedDocument with:
      - raw_text: str
      - sections: list[Section]  (name, text, page_start, page_end)
      - metadata: DocumentMetadata
      - tables: list[Table]
      - figures: list[Figure]  (with caption text)
    """
    Steps:
    1. Try pymupdf (fitz) first — best for complex layouts
    2. Fall back to pdfplumber for tables
    3. Fall back to pypdf as last resort
    4. Detect sections using regex patterns:
       - Abstract, Introduction, Related Work, Background
       - Methodology/Methods, Experiments, Results
       - Discussion, Conclusion, References, Appendix
    5. Extract tables using pdfplumber.extract_tables()
    6. Extract figure captions using heuristic: "Figure N:" pattern
    7. Extract metadata: title (largest font text on page 1),
       authors (second-largest text block), DOI (regex),
       year (4-digit in header/footer), venue (conference name patterns)
    8. Detect multi-column layout and handle column ordering
    9. Clean extracted text: remove hyphenation at line ends,
       fix ligatures (ﬁ→fi, ﬂ→fl), normalize unicode

  Also implement:
  - detect_language(text) → str  (langdetect)
  - extract_references(text) → list[Reference]  (parse bibliography)
  - extract_math_equations(text) → list[str]  (LaTeX-style)

2B. Web Scraper (ingestion/web_scraper.py)
─────────────────────────────────────────
Implement class WebScraper:

  async def scrape_url(self, url: str) -> ProcessedDocument:
    Steps:
    1. Try trafilatura.fetch_url + trafilatura.extract() first
       (best for article-style content)
    2. If trafilatura returns None or <500 chars:
       fall back to Playwright (handles JS-rendered pages)
    3. Parse with BeautifulSoup — extract: title, meta description,
       main content area (article, main, .content selectors)
    4. Detect and scrape ArXiv PDFs automatically:
       if "arxiv.org/abs/" in url → convert to PDF url and
       call PDFProcessor
    5. Respect robots.txt (use urllib.robotparser)
    6. Rate limit: 1 req/sec per domain (token bucket)
    7. Handle paywalled content gracefully (return partial)

  async def scrape_arxiv(self, arxiv_id: str) -> ProcessedDocument:
    - Download PDF from https://arxiv.org/pdf/{arxiv_id}
    - Also fetch abstract page for structured metadata
    - Parse authors, title, abstract, categories, date

2C. Chunking Strategies (ingestion/chunker.py)
───────────────────────────────────────────────
Implement class SmartChunker with these strategies:

  Strategy 1: RECURSIVE
    - Split on "\n\n" → "\n" → ". " → " " in priority order
    - Respect chunk_size and chunk_overlap from settings
    - Never split mid-sentence

  Strategy 2: SEMANTIC
    - Use sentence-transformers to embed each sentence
    - Compute cosine similarity between adjacent sentences
    - Split where similarity drops below threshold (0.7)
    - Merge small chunks below min_size (100 chars)

  Strategy 3: SECTION-AWARE (default for research papers)
    - Chunk within section boundaries — never cross sections
    - Keep Abstract as a single chunk (usually < 512 chars)
    - Split Methods/Results/Discussion with recursive strategy
    - Keep figure captions attached to their nearest paragraph

  Strategy 4: SLIDING WINDOW
    - Fixed-size windows with configurable overlap
    - Good for short documents without clear structure

  Every chunk must carry this metadata:
    ChunkMetadata(
      doc_id: str,
      chunk_id: str,  # uuid
      source_file: str,
      section: str,
      page_start: int,
      page_end: int,
      char_start: int,
      char_end: int,
      chunk_index: int,
      total_chunks: int,
      is_table: bool,
      is_caption: bool,
    )

2D. Embedder (ingestion/embedder.py)
────────────────────────────────────
Implement class EmbedderFactory that returns the right embedder:

  class BGEEmbedder:
    - Model: BAAI/bge-large-en-v1.5
    - Batch size: 32
    - Normalize embeddings to unit length
    - Use "Represent this sentence for searching: " prefix for queries
    - Use no prefix for documents (BGE convention)
    - Support CPU/CUDA/MPS device selection
    - Cache model weights on disk

  class OpenAIEmbedder:
    - Model: text-embedding-3-large (3072 dims)
    - Batch API calls in groups of 100
    - Handle rate limits with exponential backoff (tenacity)

  class CohereEmbedder:
    - Model: embed-english-v3.0
    - Use input_type="search_document" for docs
    - Use input_type="search_query" for queries

  All embedders must implement:
    def embed_documents(self, texts: list[str]) -> np.ndarray
    def embed_query(self, text: str) -> np.ndarray

2E. Ingestion Pipeline Orchestrator (ingestion/pipeline.py)
────────────────────────────────────────────────────────────
Implement class IngestionPipeline:

  async def ingest(
    self,
    source: str | Path | bytes,
    source_type: Literal["pdf","url","csv","json","docx"],
    metadata_override: dict | None = None,
  ) -> IngestionResult:

    Full pipeline:
    1. Route to correct processor (PDF/Web/CSV)
    2. Extract text + structure
    3. Run chunking strategy
    4. Generate embeddings (batched)
    5. Extract entities for knowledge graph:
       - Named entities (spaCy or GLiNER)
       - Relationships: "X uses Y", "X outperforms Y", "X is a Y"
       - Dataset names, model names, metric names
    6. Store in all backends:
       - ChromaDB: embeddings + chunk metadata
       - SQLite: document metadata + chunk index
       - BM25: update inverted index
       - Neo4j: entity nodes + relationship edges
    7. Invalidate semantic cache for affected queries
    8. Return IngestionResult with stats

  Also implement:
    async def ingest_batch(self, sources: list) -> list[IngestionResult]
    async def delete_document(self, doc_id: str) -> bool
    async def update_document(self, doc_id: str, source) -> IngestionResult
"""

# ============================================================
# PHASE 3 — STORAGE LAYER
# ============================================================

"""
3A. Vector Store Abstraction (storage/vector_store.py)
───────────────────────────────────────────────────────
Create an abstract base class VectorStore with implementations
for ChromaDB and pgvector:

  class VectorStore(ABC):
    @abstractmethod
    async def add(self, chunks: list[Chunk]) -> None
    @abstractmethod
    async def search(
      self,
      query_embedding: np.ndarray,
      k: int,
      filter: dict | None,
    ) -> list[SearchResult]
    @abstractmethod
    async def delete(self, doc_id: str) -> None
    @abstractmethod
    async def get_stats(self) -> StoreStats

  class ChromaDBStore(VectorStore):
    - Use chromadb.AsyncHttpClient for remote
    - Use chromadb.EphemeralClient for testing
    - Collection: research_papers
    - Include metadata: doc_id, chunk_id, page, section, source
    - Support metadata filtering (where clause)
    - HNSW index with m=16, ef_construction=100

  class PgVectorStore(VectorStore):
    - Use pgvector extension on PostgreSQL
    - Use asyncpg for async queries
    - CREATE INDEX USING ivfflat (embedding vector_cosine_ops)
    - Support hybrid filter queries (vector + SQL WHERE)

3B. BM25 Store (storage/bm25_store.py)
────────────────────────────────────────
Implement class BM25Store:
  - Use rank-bm25 BM25Okapi
  - Persist index to disk (pickle + rebuild on startup)
  - Tokenization: lower, remove stopwords, stem (nltk)
  - Support incremental updates (add/remove documents)
  - Thread-safe with RLock for concurrent queries

  def search(self, query: str, k: int) -> list[BM25Result]
  def add_chunks(self, chunks: list[Chunk]) -> None
  def remove_document(self, doc_id: str) -> None
  def rebuild_index(self) -> None

3C. Knowledge Graph (storage/graph_store.py)
──────────────────────────────────────────────
Implement class Neo4jGraphStore:

  Node types:
    (:Document {doc_id, title, year, venue, doi})
    (:Author {name, affiliation})
    (:Chunk {chunk_id, text, section, page})
    (:Entity {name, type, description})  # methods, datasets, etc.
    (:Concept {name, domain})            # higher-level topics

  Relationship types:
    (:Document)-[:HAS_CHUNK]->(:Chunk)
    (:Document)-[:WRITTEN_BY]->(:Author)
    (:Document)-[:CITES]->(:Document)
    (:Document)-[:INTRODUCES]->(:Entity)
    (:Document)-[:USES]->(:Entity)
    (:Entity)-[:IS_A]->(:Concept)
    (:Entity)-[:OUTPERFORMS {metric, value}]->(:Entity)
    (:Entity)-[:EVALUATED_ON]->(:Entity)

  Implement:
    async def add_document_graph(self, doc: ProcessedDocument) -> None
    async def search_related(self, query: str, depth: int=2) -> list[Chunk]
    async def find_entity_neighbors(self, entity: str) -> list[Node]
    async def get_citation_network(self, doc_id: str) -> Graph
    async def cypher_query(self, cypher: str) -> list[dict]

  For entity extraction use a small NER model:
    - spaCy en_core_web_trf for general NER
    - Custom patterns for ML/CS entities (GLiNER)
    - Extract: Model names, Dataset names, Metrics, Methods

3D. Semantic Cache (storage/cache_store.py)
────────────────────────────────────────────
Implement class SemanticCache:

  def __init__(self, redis_url: str, threshold: float = 0.92):
    - Connect to Redis
    - Use redisvl or manual vector storage for cache keys

  async def get(self, query: str, query_embedding: np.ndarray) -> CachedResponse | None:
    Steps:
    1. Search Redis for nearest stored query embedding
    2. If cosine similarity > threshold → cache hit
    3. Return cached CachedResponse with TTL check
    4. Log cache hit/miss for observability

  async def set(self, query: str, query_embedding: np.ndarray, response: QueryResponse) -> None:
    - Store (embedding, response, timestamp, ttl) in Redis
    - Serialize response with msgpack for efficiency

  async def invalidate_by_doc(self, doc_id: str) -> int:
    - Remove all cache entries that used chunks from doc_id
    - Return number of entries invalidated
"""

# ============================================================
# PHASE 4 — RETRIEVAL ENGINE
# ============================================================

"""
4A. Hypothetical Document Embeddings (retrieval/hyde_retriever.py)
───────────────────────────────────────────────────────────────────
Implement class HyDERetriever:

  HyDE improves retrieval by generating a HYPOTHETICAL
  answer to the query, then embedding that to search.

  async def retrieve(self, query: str, k: int) -> list[SearchResult]:
    1. Generate hypothetical document using LLM:
       prompt = f"Write a short research paper excerpt that would
                  answer the following question: {query}"
    2. Embed the hypothetical document (not the query)
    3. Search vector store with that embedding
    4. Return top-k results
    5. Also run standard query embedding in parallel
    6. Combine both result sets before returning

4B. ColBERT Multi-Vector Retrieval (retrieval/colbert_retriever.py)
────────────────────────────────────────────────────────────────────
Implement class ColBERTRetriever:

  ColBERT stores per-token embeddings and does late interaction.

  def index_chunks(self, chunks: list[Chunk]) -> None:
    - Use colbert-ir/colbertv2.0 tokenizer
    - Store token-level embeddings for each chunk in ChromaDB
      with chunk_id + token_position as composite key

  def search(self, query: str, k: int) -> list[SearchResult]:
    - Tokenize query → per-token embeddings
    - MaxSim: for each query token, find max similarity
      across all document tokens
    - Sum MaxSim scores across query tokens → chunk score
    - Return top-k by ColBERT score
    - This is computationally expensive — only use on
      reranked candidate set (top 20), not full corpus

4C. RRF Fusion (retrieval/fusion.py)
──────────────────────────────────────
Implement class RetrievalFusion:

  def reciprocal_rank_fusion(
    self,
    result_lists: list[list[SearchResult]],
    k: int = 60,
    weights: list[float] | None = None,
  ) -> list[SearchResult]:
    """
    RRF formula: score(d) = Σ 1/(k + rank_i(d))
    Optional: weight each retriever's contribution
    """
    1. Build a dict of doc_id → cumulative RRF score
    2. For each result list:
       - Assign ranks 1..n
       - score += weight * (1 / (k + rank))
    3. Sort by cumulative score descending
    4. Deduplicate: prefer the result with highest individual score
    5. Return top candidates (typically k_vec + k_bm25 before rerank)

  def weighted_combination(
    self,
    vector_results: list[SearchResult],
    bm25_results: list[SearchResult],
    alpha: float = 0.6,  # weight for vector search
  ) -> list[SearchResult]:
    """
    Normalize scores then combine: score = alpha*vec + (1-alpha)*bm25
    """

  def enforce_diversity(
    self,
    results: list[SearchResult],
    max_per_doc: int = 2,
  ) -> list[SearchResult]:
    """
    Prevent one document from dominating — cap chunks per doc.
    Uses MMR (Maximal Marginal Relevance) to promote diversity.
    """
    MMR: select next chunk that maximizes:
      λ * relevance_to_query - (1-λ) * max_similarity_to_selected
    λ = 0.7 balances relevance and diversity

4D. Cross-Encoder Reranker (retrieval/reranker.py)
────────────────────────────────────────────────────
Implement class CrossEncoderReranker:

  def __init__(self):
    - Primary: BAAI/bge-reranker-v2-m3 (best quality)
    - Fallback: cross-encoder/ms-marco-MiniLM-L-6-v2 (faster)
    - Batch predictions with batch_size=16
    - Cache predictions for identical (query, chunk) pairs

  def rerank(
    self,
    query: str,
    candidates: list[SearchResult],
    top_k: int = 5,
  ) -> list[SearchResult]:
    1. Create pairs: [(query, chunk.text) for chunk in candidates]
    2. Predict relevance scores in batches
    3. Attach scores back to SearchResult objects
    4. Filter below rerank_threshold (default 0.3)
    5. Sort descending, return top_k
    6. Log reranking metrics (how many passed threshold)

4E. Hybrid Engine Orchestrator (retrieval/hybrid_engine.py)
────────────────────────────────────────────────────────────
Implement class HybridRetrievalEngine:

  async def retrieve(
    self,
    query: str,
    query_embedding: np.ndarray,
    k_final: int,
    filters: RetrievalFilters,
    use_hyde: bool = False,
    use_graph: bool = True,
    use_colbert: bool = False,
  ) -> RetrievalResult:

    Full pipeline:
    1. Run in PARALLEL (asyncio.gather):
       - Vector search (k_vector candidates)
       - BM25 search (k_bm25 candidates)
       - Graph retrieval (k_graph candidates) [if use_graph]
       - HyDE retrieval (k_vector candidates) [if use_hyde]

    2. Fuse results with RRF
    3. Apply metadata filters (paper_ids, year_range, sections)
    4. Apply diversity enforcement (max_per_doc=2)
    5. Rerank with cross-encoder → top k_rerank_candidates
    6. Optionally run ColBERT on reranked set
    7. Apply quality threshold filter
    8. Return RetrievalResult with:
       - chunks: list[Chunk] (final top_k)
       - retrieval_scores: dict[str, float]
       - source_breakdown: dict (how many from each retriever)
       - latency_ms: float
"""

# ============================================================
# PHASE 5 — ADAPTIVE QUALITY CONTROLLER
# ============================================================

"""
5A. Quality Scorer (adaptive/quality_scorer.py)
────────────────────────────────────────────────
Implement class RetrievalQualityScorer:

  def score(
    self,
    query: str,
    query_embedding: np.ndarray,
    results: list[Chunk],
  ) -> QualityMetrics:

    Compute these metrics:

    relevance_score:
      Mean of cross-encoder scores across top-k chunks.
      If cross-encoder unavailable: mean cosine similarity.

    diversity_score:
      unique_docs / total_chunks
      + MMR diversity component (avg pairwise distance
        between selected chunk embeddings)
      Range [0, 1], higher = more diverse sources

    coverage_score:
      Fraction of query keywords found in retrieved context.
      Use TF-IDF to weight keywords by query importance.
      Also check if named entities from query appear in results.

    completeness_score (for multi-part questions):
      For each detected sub-topic in the query,
      check if at least one chunk addresses it.
      Use NLI model to check entailment.

    overall_quality:
      Weighted combination:
        0.4 * relevance + 0.25 * diversity +
        0.20 * coverage + 0.15 * completeness

    Return QualityMetrics dataclass with all scores
    and a list of identified issues.

5B. Adaptive Controller (adaptive/adaptive_controller.py)
──────────────────────────────────────────────────────────
Implement class AdaptiveRetrievalController:

  async def optimize_retrieval(
    self,
    query: str,
    initial_results: RetrievalResult,
    quality: QualityMetrics,
    attempt: int,
  ) -> RetrievalParameters:
    """
    Decide what to adjust based on quality metrics.
    Return new RetrievalParameters for next attempt.
    """

    Adjustment rules:

    if quality.relevance_score < 0.4:
      params.k_vector *= 1.5        # cast wider net
      params.use_hyde = True        # try HyDE
      params.rerank_threshold *= 0.8 # lower threshold

    if quality.diversity_score < 0.35:
      params.max_per_doc = 1        # hard diversity cap
      params.use_graph = True       # graph often spans docs

    if quality.coverage_score < 0.45:
      params.k_bm25 *= 1.5         # more keyword matching
      reformulated = await self.reformulator.expand_query(query)
      params.query = reformulated

    if attempt >= 2:
      params.use_colbert = True     # expensive but accurate

    return params

5C. Query Reformulation (adaptive/query_reformulator.py)
─────────────────────────────────────────────────────────
Implement class QueryReformulator:

  async def expand_query(self, query: str) -> str:
    """Use LLM to add synonyms and related terms"""
    prompt = """Expand this search query with related terms,
    synonyms, and alternative phrasings. Return only the
    expanded query, no explanation.
    Query: {query}"""

  async def step_back(self, query: str) -> str:
    """Generate a more abstract version (step-back prompting)"""
    prompt = """What is the more general question behind:
    '{query}'? Return only the general question."""

  async def generate_subqueries(
    self, query: str, n: int = 3
  ) -> list[str]:
    """Multi-query retrieval: generate N alternative forms"""

  async def decompose_multihop(
    self, query: str
  ) -> list[str]:
    """Break complex query into sequential sub-questions"""
    prompt = """Break this complex research question into
    2-5 simpler sub-questions that can be answered
    independently. Return as JSON:
    {"sub_questions": ["...", "...", ...]}
    Question: {query}"""
    Return validated list of sub-questions.

5D. Corrective RAG (adaptive/corrective_rag.py)
─────────────────────────────────────────────────
Implement class CorrectiveRAG:

  async def run(
    self,
    query: str,
    initial_result: QueryResponse,
    retrieved_chunks: list[Chunk],
  ) -> QueryResponse:
    """
    CRAG pipeline:
    1. Evaluate each retrieved chunk for relevance
    2. Classify chunks: CORRECT | AMBIGUOUS | INCORRECT
    3. If too many INCORRECT → trigger knowledge refinement
    4. Re-retrieve with refined strategy
    5. Regenerate answer with corrected context
    """

    def classify_chunk(self, query: str, chunk: Chunk) -> str:
      """
      Use NLI model or LLM to classify:
      - CORRECT: chunk directly answers query aspect
      - AMBIGUOUS: chunk tangentially related
      - INCORRECT: chunk irrelevant or contradictory
      """

    async def refine_knowledge(self, query, bad_chunks) -> list[Chunk]:
      """
      When retrieval quality is poor:
      1. Extract key missing concepts from bad chunks
      2. Reformulate query focusing on those concepts
      3. Run fresh retrieval with expanded parameters
      4. Add web search results if available (Tavily API)
      """
"""

# ============================================================
# PHASE 6 — REASONING ENGINE
# ============================================================

"""
6A. Query Analyzer (reasoning/query_analyzer.py)
─────────────────────────────────────────────────
Implement class QueryAnalyzer:

  def analyze(self, query: str) -> QueryAnalysis:
    Returns QueryAnalysis(
      query_type: Literal[
        "simple_fact",       # What is X?
        "comparative",       # Compare X and Y
        "multi_hop",         # Requires chaining facts
        "causal",            # Why does X cause Y?
        "procedural",        # How to do X?
        "temporal",          # Evolution of X over time
        "quantitative",      # Metrics, numbers, stats
        "survey",            # Broad overview of field
      ],
      complexity: Literal["low", "medium", "high"],
      entities: list[str],       # detected entities
      requires_synthesis: bool,  # needs multi-doc reasoning
      is_ambiguous: bool,
      suggested_mode: str,       # basic|multihop|comparison
      estimated_sources_needed: int,
    )

    Detection heuristics:
    - "compare", "vs", "difference between" → comparative
    - "why", "cause", "because" → causal
    - "how to", "steps to" → procedural
    - Multiple named entities + complex structure → multi_hop
    - "survey", "overview", "landscape" → survey
    - Keywords from multiple distinct concepts → multi_hop

6B. Multi-Hop Reasoning (reasoning/chain_of_thought.py)
────────────────────────────────────────────────────────
Implement class MultiHopReasoner:

  async def reason(
    self,
    query: str,
    analysis: QueryAnalysis,
    retrieval_engine: HybridRetrievalEngine,
  ) -> ReasoningResult:

    For MULTI_HOP:
    1. Decompose query into sub-questions
    2. For each sub-question:
       a. Retrieve relevant chunks
       b. Generate partial answer with citations
       c. Store (sub_question, answer, sources) in context
    3. Pass ALL partial answers + context to final synthesis
    4. Generate comprehensive answer
    5. Track full reasoning trace for transparency

    For SURVEY:
    1. Identify 5-8 key aspects of the topic
    2. Retrieve evidence for each aspect in parallel
    3. Synthesize into structured literature review
    4. Auto-generate section headings

    For COMPARATIVE:
    1. Identify entities to compare
    2. Extract attributes for each entity in parallel
    3. Build comparison matrix
    4. Generate side-by-side narrative

    CoT prompt template:
    """
    You are a research assistant. Think step by step.

    Question: {query}

    Retrieved Context:
    {context}

    Reasoning steps:
    1. First, identify what information is needed...
    2. From the context, I can see that...
    3. Combining these facts...
    4. Therefore, the answer is...

    Final Answer: [your comprehensive answer here]

    Citations: [doc_id, page, exact quote for each claim]
    Confidence: [HIGH|MEDIUM|LOW]
    Limitations: [what information was missing or uncertain]
    """

6C. Self-Verifier (reasoning/self_verifier.py)
───────────────────────────────────────────────
Implement class SelfVerifier:

  async def verify(
    self,
    query: str,
    answer: str,
    retrieved_chunks: list[Chunk],
  ) -> VerificationResult:

    Run these checks:

    1. GROUNDING CHECK:
       For each factual sentence in answer:
       - Extract claims (NLP: SRL or LLM-based)
       - Check if claim is supported by any retrieved chunk
       - Use sentence similarity (cosine > 0.7) as support signal
       - Flag unsupported claims

    2. CITATION CHECK:
       For each citation in answer:
       - Verify cited chunk_id exists in retrieved set
       - Verify the cited claim appears in that chunk
       - Verify page number matches chunk metadata
       - Flag invalid citations

    3. CONSISTENCY CHECK:
       - Look for contradictions within the answer
       - Look for contradictions between answer and retrieved context
       - Use NLI model: if answer_sentence CONTRADICTS chunk → flag

    4. COMPLETENESS CHECK:
       - Does answer address all aspects of the question?
       - Are all entities from the query addressed?

    5. HALLUCINATION DETECTION:
       - Named entity check: are all entities in answer found in context?
       - Number/date check: all numbers should match context
       - Use FactCC or similar for formal entailment checking

    Returns VerificationResult(
      passed: bool,
      issues: list[VerificationIssue],
      corrective_action: Literal[
        "none", "re_retrieve", "regenerate",
        "expand_context", "return_with_warning"
      ],
      grounding_score: float,
      citation_accuracy: float,
    )

6D. LLM Router (reasoning/llm_router.py)
─────────────────────────────────────────
Implement class LLMRouter:

  Routing logic:
  - SIMPLE queries + short context → gpt-4o-mini (fast, cheap)
  - COMPLEX/multi-hop → gpt-4o or claude-3-5-sonnet (smart)
  - SURVEY/long output → claude-3-5-sonnet (large context)
  - COST-SENSITIVE mode → groq/llama-3-70b (free/cheap)
  - LOCAL/PRIVATE → ollama/llama3 (on-device)
  - FALLBACK chain: primary → fallback → local

  async def generate(
    self,
    messages: list[dict],
    query_type: str,
    max_tokens: int,
    stream: bool = False,
  ) -> str | AsyncGenerator:

  Use litellm for unified API:
    response = await litellm.acompletion(
      model=self.select_model(query_type),
      messages=messages,
      max_tokens=max_tokens,
      temperature=self.settings.temperature,
      stream=stream,
    )

  Implement:
  - Automatic retry with exponential backoff (tenacity)
  - Cost tracking (log tokens used per request)
  - Latency tracking per provider
  - Circuit breaker pattern (if provider fails 3x → skip)

6E. Citation Generator (reasoning/citation_generator.py)
─────────────────────────────────────────────────────────
Implement class CitationGenerator:

  def generate_citations(
    self,
    answer: str,
    retrieved_chunks: list[Chunk],
    style: Literal["apa","ieee","mla","inline"] = "inline",
  ) -> AnnotatedAnswer:
    """
    1. Parse answer into sentences
    2. For each sentence:
       - Compute similarity to all retrieved chunks
       - Assign top-1 or top-2 supporting chunks as citations
       - Only cite if similarity > citation_threshold (0.65)
    3. Format citations per style:
       - inline: [AuthorYear, p.X]
       - apa: Author, A. (Year). Title. Venue.
       - ieee: [N] A. Author, "Title," Venue, Year, pp. X-X.
    4. Generate bibliography section
    5. Verify: does cited chunk actually support the sentence?
    6. Return AnnotatedAnswer(
         text_with_inline_cites: str,
         bibliography: list[Citation],
         uncited_sentences: list[str],  # flagged for review
       )
    """

6F. Structured Output Models (reasoning/structured_output.py)
──────────────────────────────────────────────────────────────
Define ALL Pydantic models for API responses:

  class Citation(BaseModel):
    doc_id: str
    doc_title: str
    authors: list[str]
    year: int | None
    venue: str | None
    doi: str | None
    chunk_id: str
    page_numbers: list[int]
    relevant_excerpt: str   # max 200 chars
    support_score: float

  class SubQuestion(BaseModel):
    question: str
    answer: str
    sources: list[Citation]
    confidence: float

  class QueryResponse(BaseModel):
    query_id: str
    query: str
    answer: str
    answer_summary: str     # 1-2 sentence TL;DR
    answer_type: str
    citations: list[Citation]
    sub_questions: list[SubQuestion] | None
    reasoning_trace: list[str] | None
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    grounding_score: float
    retrieval_quality: float
    warnings: list[str]
    latency_ms: float
    token_usage: dict[str, int]
    model_used: str
    corrective_iterations: int
    cached: bool
"""

# ============================================================
# PHASE 7 — EVALUATION FRAMEWORK
# ============================================================

"""
7A. RAGAS Evaluation (evaluation/ragas_evaluator.py)
──────────────────────────────────────────────────────
Implement class RAGASEvaluator:

  Metrics to compute using ragas library:
  1. Faithfulness: Is the answer supported by the context?
  2. Answer Relevancy: Is the answer relevant to the question?
  3. Context Precision: Is retrieved context relevant?
  4. Context Recall: Does context cover ground truth?
  5. Answer Correctness: Factual + semantic similarity to GT

  async def evaluate_single(
    self,
    question: str,
    answer: str,
    contexts: list[str],
    ground_truth: str | None,
  ) -> RAGASMetrics

  async def evaluate_dataset(
    self,
    dataset: list[EvalSample],
    batch_size: int = 10,
  ) -> EvalReport

  Built-in eval dataset: load QASPER benchmark
  (scientific paper QA dataset) for auto-evaluation.

7B. Retrieval Metrics (evaluation/retrieval_metrics.py)
────────────────────────────────────────────────────────
Implement:

  def precision_at_k(relevant: set, retrieved: list, k: int) -> float
  def recall_at_k(relevant: set, retrieved: list, k: int) -> float
  def mean_reciprocal_rank(relevant: set, retrieved: list) -> float
  def ndcg_at_k(relevance_scores: list[int], k: int) -> float
  def mean_average_precision(relevant: set, retrieved: list) -> float

  Also implement EmbeddingDriftDetector:
  - Track embedding space distribution over time
  - Alert when new documents are very different from existing corpus
  - Use MMD (Maximum Mean Discrepancy) for distribution comparison

7C. Benchmark Runner (evaluation/benchmark_runner.py)
───────────────────────────────────────────────────────
Implement class BenchmarkRunner:

  async def run_full_benchmark(self) -> BenchmarkReport:
    1. Load eval dataset from data/eval_datasets/
    2. Run each query through the full RAG pipeline
    3. Measure: RAGAS metrics, retrieval metrics, latency
    4. Compare configurations (ablation study):
       - vector_only, bm25_only, hybrid, hybrid+rerank,
         hybrid+rerank+adaptive, full_system
    5. Generate HTML report with charts
    6. Save results to eval_results/TIMESTAMP.json

  Datasets to support:
  - QASPER (scientific QA)
  - NarrativeQA (document QA)
  - Custom: data/eval_datasets/custom_qa.jsonl
"""

# ============================================================
# PHASE 8 — FASTAPI BACKEND & WEBSOCKET STREAMING
# ============================================================

"""
8A. Main FastAPI App (main.py)
───────────────────────────────
Create the FastAPI application with:

  app = FastAPI(
    title="Advanced Hybrid RAG API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
  )

  Middleware stack (in order):
  1. CORSMiddleware (allow frontend origin)
  2. RateLimitMiddleware (slowapi: 100/minute per IP)
  3. AuthMiddleware (JWT or API key validation)
  4. RequestLoggingMiddleware (loguru structured logging)
  5. TracingMiddleware (OpenTelemetry spans)
  6. CompressionMiddleware (GZip for large responses)

  Startup events:
  1. Initialize all storage backends (ChromaDB, Redis, Neo4j)
  2. Load embedding model into memory
  3. Load BM25 index from disk
  4. Load reranker model
  5. Initialize Celery worker connections
  6. Health check all dependencies
  7. Log startup summary

  Error handlers:
  - 404: Return JSON with helpful message
  - 422: Validation error with field details
  - 429: Rate limit with retry-after header
  - 500: Log full traceback, return safe error message

8B. Ingest Endpoint (api/routes/ingest.py)
────────────────────────────────────────────
POST /api/ingest
  Body: multipart/form-data with:
    - file: UploadFile (PDF/DOCX)
    - metadata: JSON string (optional title/year/author overrides)
    - async_mode: bool (return task_id for background processing)

  Response (sync):
    {
      "doc_id": "uuid",
      "title": "...",
      "chunks_created": 247,
      "entities_extracted": 43,
      "ingestion_time_ms": 3421,
      "warnings": []
    }

  Response (async):
    {"task_id": "uuid", "status": "queued"}

POST /api/ingest/url
  Body: {"url": "https://arxiv.org/abs/2005.11401"}

POST /api/ingest/batch
  Body: {"urls": [...], "async": true}

GET /api/ingest/status/{task_id}
  Returns Celery task status + progress

8C. Query Endpoint (api/routes/query.py)
─────────────────────────────────────────
POST /api/query
  Body:
    {
      "query": "What datasets were used to evaluate BERT?",
      "mode": "auto",              # auto|basic|multihop|comparison
      "filters": {
        "paper_ids": [],           # restrict to specific papers
        "year_range": [2018, 2024],
        "sections": ["Methods", "Results"],
        "min_relevance": 0.4
      },
      "options": {
        "use_hyde": false,
        "use_graph": true,
        "use_colbert": false,
        "enable_adaptive": true,
        "enable_verification": true,
        "citation_style": "inline",
        "max_sources": 5,
        "stream": false,
        "model": null              # null = auto-route
      }
    }

  Response: QueryResponse (from structured_output.py)

POST /api/query/stream
  Same body as /api/query but response is SSE stream:
  - data: {"type": "status", "message": "Retrieving..."}
  - data: {"type": "chunk", "text": "..."}
  - data: {"type": "citation", "citation": {...}}
  - data: {"type": "complete", "response": QueryResponse}
  - data: {"type": "error", "message": "..."}

WebSocket /ws/query
  Bidirectional: send query, receive streaming response
  Also supports: cancel query mid-stream

8D. Papers Management (api/routes/papers.py)
──────────────────────────────────────────────
GET /api/papers
  Returns: list of all ingested documents with metadata

GET /api/papers/{doc_id}
  Returns: full document metadata + chunk count + entity list

DELETE /api/papers/{doc_id}
  Removes from ALL stores (ChromaDB, BM25, Neo4j, SQLite)
  Invalidates semantic cache entries using this doc

GET /api/papers/{doc_id}/chunks
  Returns: list of chunks with text + metadata

GET /api/papers/search?q=bert
  Full-text search across paper titles and abstracts

8E. Graph Endpoint (api/routes/graph.py)
─────────────────────────────────────────
GET /api/graph/entities
  Returns: all entity nodes with type and doc count

GET /api/graph/entity/{name}
  Returns: entity + all relationships + connected docs

GET /api/graph/citation-network
  Returns: D3-compatible graph (nodes + edges) of citations

POST /api/graph/query
  Body: {"cypher": "MATCH (n:Entity)-[:OUTPERFORMS]->(m) RETURN n,m"}
  Admin-only Cypher query endpoint

8F. Evaluation Endpoint (api/routes/eval.py)
──────────────────────────────────────────────
POST /api/evaluate
  Run RAGAS evaluation on a single Q&A pair
  Body: {question, answer, contexts, ground_truth}
  Returns: RAGASMetrics

GET /api/evaluate/benchmark
  Trigger full benchmark run (async)

GET /api/evaluate/results
  Return latest benchmark results

GET /api/stats
  System stats: total papers, chunks, queries,
  cache hit rate, avg latency, model usage breakdown
"""

# ============================================================
# PHASE 9 — REACT FRONTEND
# ============================================================

"""
Build a production-quality React 18 frontend using:
  - TypeScript (strict mode)
  - Vite as bundler
  - Tailwind CSS + shadcn/ui components
  - Zustand for global state
  - TanStack Query (React Query) for data fetching
  - React Hook Form + Zod for form validation
  - D3.js for knowledge graph visualization
  - Recharts for metrics/evaluation charts

9A. ChatInterface.tsx
──────────────────────
Features:
  - Messages list with user/assistant bubble styling
  - Collapsible reasoning trace panel (shows sub-questions)
  - Streaming text display (SSE / WebSocket)
  - Typing indicator during generation
  - Code block syntax highlighting in answers
  - Copy button on assistant messages
  - Thumbs up/down rating per message
  - "Show sources" toggle that expands citation panel

9B. DocumentUpload.tsx
───────────────────────
Features:
  - Drag-and-drop zone + file picker
  - Support: PDF, DOCX, URL input tab
  - Progress bar during upload + processing
  - Processing stages display: "Extracting text... Chunking...
    Generating embeddings... Building graph..."
  - Uploaded documents list with delete option
  - Per-document stats (chunks, entities)

9C. CitationViewer.tsx
───────────────────────
Features:
  - Slide-in panel showing all citations for current answer
  - Each citation card: title, authors, year, page, excerpt
  - Highlighted relevant excerpt from the source
  - "Open full paper" button
  - Citation confidence indicator (color-coded)
  - Export as BibTeX button

9D. GraphViewer.tsx
─────────────────────
Features:
  - D3.js force-directed graph of entities + relations
  - Color-coded by node type (Document=blue, Entity=amber, etc.)
  - Hover: show node details tooltip
  - Click: highlight connected nodes
  - Zoom + pan
  - Filter by: entity type, document, relationship type
  - Search to highlight specific nodes

9E. EvalDashboard.tsx
──────────────────────
Features:
  - Recharts bar chart: Precision@K, Recall@K, MRR
  - Line chart: latency over time
  - Pie chart: cache hit rate
  - Table: top-K comparison (vector vs hybrid vs full system)
  - Trigger benchmark button
  - Real-time metrics refresh

9F. SettingsPanel.tsx
──────────────────────
Features:
  - Model selector (dropdown: GPT-4o, Claude, Llama, etc.)
  - Retrieval sliders (K vector, K BM25, K final)
  - Toggle switches: HyDE, CRAG, Adaptive, Graph
  - Chunk strategy selector
  - Citation style selector
  - Debug mode toggle (shows retrieval scores on responses)
  - Export settings as JSON / import JSON

9G. Zustand Store (store/ragStore.ts)
───────────────────────────────────────
State:
  - messages: Message[]
  - documents: Document[]
  - settings: RAGSettings
  - isStreaming: boolean
  - currentQuery: string
  - evaluationResults: EvalResults | null
  - graphData: GraphData | null

Actions:
  - sendQuery(query, settings) → handles SSE streaming
  - uploadDocument(file | url)
  - deleteDocument(docId)
  - updateSettings(partial<RAGSettings>)
  - rateMessage(messageId, rating)
"""

# ============================================================
# PHASE 10 — STREAMLIT DEMO APP
# ============================================================

"""
Build streamlit_demo/app.py with these pages:

Page 1: Research Assistant (main)
  - Sidebar: uploaded papers list + upload widget
  - Main: chat interface with full query options
  - Show: retrieved chunks, citations, reasoning trace
  - Debug panel: raw retrieval scores, model latency

Page 2: Knowledge Graph Explorer
  - st_agraph or pyvis network visualization
  - Entity search + highlight
  - Relationship filter checkboxes

Page 3: Evaluation Dashboard
  - Run RAGAS evaluation on uploaded test set
  - Display metrics table + radar chart (plotly)
  - Ablation study comparison table

Page 4: System Configuration
  - All retrieval parameters as sliders/dropdowns
  - Model selection
  - Chunking strategy picker

Implement as multi-page using st.navigation() (Streamlit 1.36+).
Cache expensive operations with @st.cache_resource.
Use st.session_state for conversation history.
"""

# ============================================================
# PHASE 11 — DOCKER & DEPLOYMENT
# ============================================================

"""
11A. docker-compose.yml — Full stack:

services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment: [all env vars]
    depends_on: [chromadb, redis, neo4j, postgres]
    volumes: ["./data:/app/data"]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]

  streamlit:
    build: ./streamlit_demo
    ports: ["8501:8501"]
    depends_on: [backend]

  chromadb:
    image: chromadb/chroma:latest
    ports: ["8001:8000"]
    volumes: ["chroma_data:/chroma/chroma"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    command: redis-server --save 60 1 --loglevel warning
    volumes: ["redis_data:/data"]

  neo4j:
    image: neo4j:5-community
    ports: ["7474:7474", "7687:7687"]
    environment:
      NEO4J_AUTH: neo4j/password
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
    volumes: ["neo4j_data:/data"]

  postgres:
    image: ankane/pgvector:latest  # postgres + pgvector
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: ragdb
      POSTGRES_USER: rag
      POSTGRES_PASSWORD: password
    volumes: ["pg_data:/var/lib/postgresql/data"]

  celery_worker:
    build: ./backend
    command: celery -A tasks worker --loglevel=info --concurrency=4
    depends_on: [redis, backend]

  celery_flower:
    image: mher/flower
    ports: ["5555:5555"]
    command: celery flower --broker=redis://redis:6379/0

  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes: ["./nginx.conf:/etc/nginx/conf.d/default.conf"]
    depends_on: [backend, frontend]

  phoenix:   # Arize Phoenix observability
    image: arizephoenix/phoenix:latest
    ports: ["6006:6006"]

11B. Makefile targets:

make dev          → docker-compose -f docker-compose.dev.yml up
make prod         → docker-compose up -d
make ingest URL=https://arxiv.org/abs/XXX
make benchmark    → run evaluation suite
make test         → pytest tests/
make logs         → docker-compose logs -f backend
make shell        → docker exec -it backend bash
make clean        → remove all volumes and containers
"""

# ============================================================
# PHASE 12 — ADVANCED FEATURES (BEYOND THE PDF)
# ============================================================

"""
These features go BEYOND what the original project described.
Implement them after Phases 1-11 are complete.

12A. MULTI-MODAL SUPPORT
─────────────────────────
File: ingestion/multimodal_processor.py

  - Figure extraction: use pymupdf to extract images from PDFs
  - Figure understanding: pass to GPT-4o-vision or LLaVA
  - Table extraction: pdfplumber.extract_tables() + to markdown
  - Equation detection: detect $ ... $ and \[ ... \] patterns
  - Store figure descriptions + table markdown as additional chunks
  - Link figure chunks to their caption chunks

12B. ACTIVE LEARNING FROM FEEDBACK
────────────────────────────────────
File: api/routes/feedback.py + adaptive/feedback_learner.py

  POST /api/feedback
  Body: {
    query_id, rating (1-5), helpful (bool),
    corrected_answer (str | null),
    bad_citation_ids (list[str])
  }

  FeedbackLearner:
  - Store all feedback in PostgreSQL
  - Low-rated responses → add to "hard negatives" training set
  - High-rated retrieval → boost those chunk embeddings in index
  - Use feedback to auto-tune RRF weights (vector_weight, bm25_weight)
  - Nightly fine-tuning job: RLHF-style fine-tune embedder on feedback

12C. REAL-TIME ARXIV MONITORING
────────────────────────────────
File: ingestion/arxiv_monitor.py

  Background Celery task that:
  1. Polls arxiv.org RSS feeds for configured categories
     (cs.AI, cs.CL, cs.IR, cs.LG, etc.)
  2. Fetches new papers daily
  3. Filters by: keyword list, author list, citation threshold
  4. Auto-ingests filtered papers
  5. Sends Slack/email notification with summary of new papers
  6. Generates daily digest: "3 new papers on RAG systems today"

  API endpoints:
  POST /api/monitor/arxiv  → configure monitoring
  GET  /api/monitor/digest → get latest digest

12D. COLLABORATIVE ANNOTATIONS
────────────────────────────────
File: api/routes/annotations.py + storage/annotation_store.py

  POST /api/annotations
    {doc_id, chunk_id, text, annotation, user_id, public: bool}

  GET /api/annotations/{doc_id}
    Returns all annotations for a document

  Features:
  - Inline annotations on specific passages
  - Team-shared annotation collections
  - Annotation search (find annotations mentioning "BERT")
  - Export annotations as JSON/CSV
  - Annotations become additional context for queries
    (if query mentions annotated concept, show annotation)

12E. AUTOMATED LITERATURE REVIEW GENERATION
────────────────────────────────────────────
File: reasoning/literature_review_generator.py

  POST /api/literature-review
  Body: {
    topic: str,
    max_papers: int = 20,
    sections: list[str] = ["background", "methods", "results", "gaps"]
  }

  Steps:
  1. Identify all relevant papers for the topic
  2. Cluster papers by methodology (k-means on embeddings)
  3. For each cluster: generate a themed paragraph
  4. Generate transitions between sections
  5. Auto-fill:
     - Introduction (what problem and why it matters)
     - Timeline (chronological evolution)
     - Methods taxonomy (comparison table)
     - Results summary (key numbers)
     - Research gaps (what's missing)
  6. Full bibliography with consistent formatting
  7. Return as: Markdown | DOCX | LaTeX

12F. QUERY PLANNING AGENT
───────────────────────────
File: reasoning/query_planning_agent.py

  For very complex queries, implement a ReAct-style agent:

  Agent tools available:
  - retrieve(query, filters) → chunks
  - search_web(query) → web results (Tavily API)
  - lookup_entity(name) → graph neighbors
  - compute(expression) → math calculations
  - compare(entity_a, entity_b, metric) → comparison

  Agent loop:
    Thought: What information do I need?
    Action: retrieve("BERT architecture details")
    Observation: [retrieved chunks]
    Thought: I need more on GPT-3 to compare...
    Action: retrieve("GPT-3 architecture details")
    Observation: [retrieved chunks]
    Thought: Now I can compare and answer.
    Action: FINAL_ANSWER("BERT uses bidirectional...")

  Max iterations: 8
  Timeout: 60 seconds
  Fallback: use standard multi-hop reasoning

12G. SEMANTIC SEARCH UI OVER GRAPH
────────────────────────────────────
Natural language → Cypher query translation:

  POST /api/graph/nl-query
  Body: {"question": "Which papers compare BERT and GPT?"}

  Steps:
  1. LLM generates Cypher:
     MATCH (d:Document)-[:MENTIONS]->(e:Entity {name: "BERT"})
     MATCH (d)-[:MENTIONS]->(e2:Entity {name: "GPT"})
     RETURN d.title, d.year ORDER BY d.year
  2. Execute against Neo4j
  3. Return structured results + visualization data

12H. DIFFERENTIAL PRIVACY FOR SENSITIVE DOCUMENTS
───────────────────────────────────────────────────
File: ingestion/privacy_processor.py

  For documents marked as sensitive:
  - Detect PII: names, emails, phone numbers, SSN
    (use Microsoft Presidio)
  - Redact or pseudonymize before embedding
  - Add noise to embeddings (DP-SGD-style Gaussian noise)
  - Separate ChromaDB collection for sensitive docs
  - Access control: only users with permission can query it

  POST /api/ingest with header: X-Privacy-Level: high

12I. CITATION GRAPH ANALYSIS
──────────────────────────────
File: analysis/citation_analysis.py

  - Build citation network from extracted references
  - Compute: PageRank, betweenness centrality per paper
  - Find: seminal papers (high in-degree)
  - Find: survey papers (high out-degree)
  - Find: research communities (Louvain clustering)
  - Timeline view: how ideas evolved across papers
  - "This paper builds on" and "This paper influenced" features

  GET /api/papers/{doc_id}/influence
  Returns: influential papers + influenced papers + centrality score
"""

# ============================================================
# PHASE 13 — TESTING STRATEGY
# ============================================================

"""
Write a comprehensive test suite covering:

UNIT TESTS (tests/unit/):

  test_chunker.py:
  - test_recursive_chunking_respects_size()
  - test_semantic_chunking_finds_boundaries()
  - test_section_aware_never_crosses_sections()
  - test_chunk_metadata_preserved()
  - test_overlap_correct()

  test_fusion.py:
  - test_rrf_correct_formula()
  - test_rrf_deduplicates()
  - test_diversity_enforcement_caps_per_doc()
  - test_weighted_combination_sums_to_one()

  test_verifier.py:
  - test_grounding_check_catches_unsupported_claims()
  - test_citation_check_validates_page_numbers()
  - test_hallucination_detection_flags_entities()
  - test_passes_when_fully_grounded()

  test_quality_scorer.py:
  - test_relevance_score_range_0_to_1()
  - test_diversity_low_when_single_doc()
  - test_coverage_penalizes_missing_keywords()

INTEGRATION TESTS (tests/integration/):

  test_pipeline.py:
  - test_full_ingestion_creates_all_stores()
  - test_delete_removes_from_all_stores()
  - test_query_returns_valid_response_structure()
  - test_multihop_decomposition_and_synthesis()
  - test_adaptive_retries_on_low_quality()
  - test_crag_corrects_bad_retrieval()
  - test_streaming_sends_sse_events()
  - test_semantic_cache_hits_on_similar_query()

E2E TESTS (tests/e2e/):
  - test_upload_and_query_full_flow()
  - test_arxiv_url_ingestion()
  - test_multi_doc_synthesis()
  - test_citation_accuracy_on_known_facts()

Use pytest-asyncio for async tests.
Use pytest-benchmark for latency regression testing.
Use httpx.AsyncClient for API testing.
"""

# ============================================================
# COPILOT EXECUTION INSTRUCTIONS
# ============================================================

"""
START HERE — send these instructions to GitHub Copilot Agent:

"I want to build the Advanced Hybrid RAG system described in
this prompt file. Please start with Phase 0 and create the
complete project scaffold first. Then I will ask you to
implement each phase one by one.

Important implementation rules:
1. Always use async/await for I/O operations
2. Every class must have proper type hints (Python 3.11+)
3. Use Pydantic v2 models for all data structures
4. Add docstrings to all public methods
5. Implement proper error handling — never bare except clauses
6. Use loguru for all logging with structured context
7. Each module must have __all__ defined
8. Use dependency injection — pass dependencies as constructor args
9. Make everything configurable through settings.py
10. Every storage operation must be idempotent

After generating each phase, ask me to review before
proceeding to the next phase."

PHASE ORDER FOR IMPLEMENTATION:
Phase 0 → Scaffold
Phase 1 → Config + Env
Phase 2 → Ingestion (start with PDF Processor)
Phase 3 → Storage (ChromaDB + BM25 first, then Neo4j + Redis)
Phase 4 → Retrieval (Vector → BM25 → Fusion → Reranker → Engine)
Phase 5 → Adaptive Controller
Phase 6 → Reasoning Engine
Phase 7 → Evaluation Framework
Phase 8 → FastAPI Backend
Phase 9 → React Frontend
Phase 10 → Streamlit Demo
Phase 11 → Docker Deploy
Phase 12 → Advanced Features (pick ones you want)
Phase 13 → Tests
"""
