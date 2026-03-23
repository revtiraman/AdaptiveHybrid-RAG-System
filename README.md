# Research Paper RAG Service

This repository is now a production-oriented baseline for a research-paper RAG system. It is built to ingest PDFs, chunk and index them, retrieve relevant passages with a local SQLite-backed vector store, and answer questions through either a deterministic local generator or OpenAI-backed generation.

The project is designed to work in two modes:

- `hash` + `extractive`: fully local, deterministic, good for development and tests.
- `openai` + `openai`: production-style retrieval and answer generation using OpenAI embeddings and the Responses API.

## What is included

- FastAPI service with health checks and typed JSON endpoints.
- CLI for ingestion, querying, ArXiv sync, evaluation runs, document listing, and serving.
- SQLite vector store with document metadata and chunk persistence.
- PDF ingestion pipeline with managed document storage under `data/documents/`.
- Smart parser fallback path (docling/marker/bbox/legacy) with extraction diagnostics.
- Claim extraction + claim-level retrieval fusion + citation-chain augmentation.
- Multi-stage self-verifier with stage scores and issue diagnostics.
- Evaluation harness for dataset-based quality regression checks.
- Frontend document structure viewer backed by debug APIs.
- Sentence-aware chunking with overlap to preserve context continuity.
- Pluggable embeddings and answer generation providers.
- Dockerfile, Makefile, env template, and unit tests.

## Architecture

The system is intentionally layered so you can replace individual components without rewriting the rest of the app:

- `research_rag.adapters.pdf_loader.PdfLoader`
  Reads PDF pages using `pypdf`.
- `research_rag.chunking.chunk_pages`
  Converts page text into overlapping chunks with page-level citation fidelity.
- `research_rag.adapters.embeddings.*`
  Turns chunks and questions into vectors. The hashing provider is deterministic and dependency-light; the OpenAI provider is production-facing.
- `research_rag.adapters.store.SqliteVectorStore`
  Persists documents and chunk embeddings in SQLite and performs cosine-similarity search.
- `research_rag.adapters.generator.*`
  Produces answers. The extractive generator is local; the OpenAI generator calls the Responses API.
- `research_rag.services.ingestion.DocumentIngestionService`
  Orchestrates file validation, copying, parsing, chunking, embedding, and indexing.
- `research_rag.services.query.RagQueryService`
  Embeds the user query, retrieves top chunks, and produces a cited answer.

## Project layout

```text
.
├── src/research_rag
│   ├── adapters
│   ├── api
│   ├── services
│   ├── bootstrap.py
│   ├── chunking.py
│   ├── cli.py
│   ├── domain.py
│   ├── logging.py
│   └── settings.py
├── tests
├── Dockerfile
├── Makefile
└── pyproject.toml
```

## Quickstart

### 1. Install dependencies

```bash
python3 -m pip install -e .
```

For development tools:

```bash
python3 -m pip install -e .[dev]
```

### 2. Configure environment

Copy `.env.example` into `.env` or export the variables manually.

Local deterministic mode:

```bash
export EMBEDDING_PROVIDER=hash
export GENERATION_PROVIDER=extractive
```

OpenAI-backed mode:

```bash
export EMBEDDING_PROVIDER=openai
export GENERATION_PROVIDER=openai
export OPENAI_API_KEY=your_key_here
export OPENAI_EMBEDDING_MODEL=text-embedding-3-small
export OPENAI_RESPONSES_MODEL=gpt-5-mini
```

SaaS mode (API keys + tenant isolation):

```bash
export API_KEYS="team-a:key-a,team-b:key-b"
```

In SaaS mode, all `/v1/*` requests require `x-api-key` (or `Authorization: Bearer ...`).
Documents are automatically tagged per tenant and queries/listing are scoped to that tenant.

### 3. Ingest your PDF

The PDF you pointed to can be ingested directly:

```bash
PYTHONPATH=src python3 -m research_rag.cli ingest \
  --pdf "/Users/revtiramantripathi/Downloads/ilovepdf_merged (2) (6).pdf"
```

This will:

- copy the PDF into `data/documents/`
- extract page text
- split pages into overlapping chunks
- embed the chunks
- persist the document and chunk index into `data/rag.sqlite3`

### 4. Query the indexed paper

```bash
PYTHONPATH=src python3 -m research_rag.cli query \
  --question "Summarize the main problem, method, and conclusions."
```

### 5. ArXiv auto-pipeline (dry run first)

```bash
PYTHONPATH=src python3 -m research_rag.cli arxiv-sync \
  --dry-run --max-results 5 --days-back 30
```

Then run without `--dry-run` to download and ingest matches.

### 6. Evaluation harness

Create a JSON dataset like this:

```json
[
  {
    "question": "What is the paper about?",
    "expected_keywords": ["retrieval", "generation"],
    "paper_ids": []
  }
]
```

Run evaluation:

```bash
PYTHONPATH=src python3 -m research_rag.cli evaluate --dataset data/eval/smoke_eval.json
```

Included stronger suite:

- `data/eval/research_eval_suite.json` (12 research-oriented cases)

Run it:

```bash
PYTHONPATH=src python3 -m research_rag.cli evaluate --dataset data/eval/research_eval_suite.json --limit 12
```

Frontend also supports this via the **Evaluation Harness** panel.

### 7. Run the API

```bash
uvicorn research_rag.api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

OpenAPI docs will be available at `http://127.0.0.1:8000/docs`.

## API endpoints

### `GET /health/live`

Basic liveness probe.

### `GET /health/ready`

Readiness probe showing storage path, provider selection, and indexed document count.

### `GET /papers`

Lists indexed documents.

### `POST /upload`

Multipart body:

- `file`: PDF file (required)
- `title`: Optional title
- `paper_id`: Optional stable ID

### `POST /query`

Request body:

```json
{
  "question": "What evaluation metrics were reported?",
  "paper_ids": ["optional-paper-id"],
  "filters": {
    "section": "optional-section"
  }
}
```

Response includes:

- answer text
- claim-level citations with page numbers and chunk identifiers
- retrieval quality, retries, and latency
- diagnostic verification payload (`supported`, `confidence`, `issues`, `stage_scores`)

### `POST /pipeline/arxiv/sync`

Triggers ArXiv fetch/filter/download/ingest pipeline.

Request body:

```json
{
  "query": "retrieval augmented generation",
  "max_results": 10,
  "days_back": 30,
  "categories": ["cs.AI", "cs.CL", "cs.LG"],
  "relevance_terms": ["rag", "retrieval", "question answering"],
  "dry_run": true
}
```

### `POST /eval/run`

Run the evaluation harness against a JSON or JSONL dataset.

```json
{
  "dataset_path": "data/eval/smoke_eval.json",
  "limit": 10
}
```

### `POST /debug/chunk-sample`

Returns sampled chunk diagnostics for a paper.

### `POST /debug/paper-structure`

Returns section-level structure stats (`chunk_count`, `claim_count`, `table_count`) and quality indicators used by the frontend structure viewer.

## Make targets

- `make install`
- `make dev`
- `make test`
- `make check`
- `make run`
- `make ingest`
- `make query`
- `make list-docs`
- `make docker-build`

## Running with Docker

Build:

```bash
docker build -t research-rag-service .
```

Run:

```bash
docker run --rm -p 8000:8000 \
  -e EMBEDDING_PROVIDER=hash \
  -e GENERATION_PROVIDER=extractive \
  -v "$(pwd)/data:/app/data" \
  research-rag-service
```

## Production notes

This repository is now structured for production work, but a few scale-up steps are still worth considering depending on traffic and data volume:

- Replace the SQLite store with `pgvector`, Qdrant, or another dedicated vector database when indexing many papers.
- Add authentication if the ingestion API should not be publicly accessible.
- Put the service behind a reverse proxy and configure TLS at the edge.
- Add background jobs for ingestion if you expect large PDFs or many concurrent uploads.
- Add metrics and tracing if you need deeper operational visibility.
- Add evaluation datasets and answer-quality regression tests before model changes.

## Local verification

The included unit tests focus on the chunker, vector store, and query pipeline. They are designed to run without external API calls.

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall src tests
```
