# Advanced Hybrid RAG

Production-focused research assistant stack with hybrid retrieval, adaptive controls, and reasoning features.

## Current implementation

- FastAPI backend with ingestion, retrieval, adaptive, reasoning, evaluation, and websocket APIs.
- React frontend scaffold with query/upload/evaluation views.
- Streamlit demo scaffold for quick local demos.
- Phase 12 advanced features wired:
	- feedback collection and stats
	- collaborative annotations
	- arXiv monitoring and digest endpoints
	- citation graph analysis endpoint
	- literature review generation endpoint
	- query planning endpoint
	- privacy redaction support in ingestion flow

## Quick start

1. Create and activate a Python environment.
2. Install backend dependencies from this directory:

```bash
pip install -e .
```

3. Run backend API:

```bash
uvicorn backend.main:create_app --factory --host 127.0.0.1 --port 8000
```

4. Optional frontend run (from frontend directory):

```bash
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

## Key API routes

- Health: GET /api/health, GET /api/health/ready
- Ingestion: POST /api/ingest, POST /api/ingest/url, POST /api/ingest/batch
- Query: POST /api/query, POST /api/query/stream
- Feedback: POST /api/feedback/, GET /api/feedback/stats
- Annotations: POST /api/annotations, GET /api/annotations/{document_id}
- Planning: POST /api/planning/react
- Monitoring: POST /api/monitor/arxiv/config, POST /api/monitor/arxiv/poll, GET /api/monitor/arxiv/digest
- Literature: POST /api/literature/review
- Analysis: POST /api/analysis/citations

## Integration details

- Ingestion privacy redaction:
	- URL ingest body supports redact_pii flag.
	- File ingest supports redact_pii query parameter.
- Query planning:
	- Query options support enable_planning.
	- Planner auto-engages for multihop and comparison modes.

## Testing

Run integration tests:

```bash
pytest tests/integration -q
```

Run all tests:

```bash
pytest -q
```

## Repository layout

- backend: FastAPI app and RAG engine modules.
- frontend: React + TypeScript client.
- streamlit_demo: Streamlit app.
- tests: unit, integration, e2e suites.
- notebooks: exploration and benchmarking.
