from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.adaptive.quality_scorer import QualityMetrics
from backend.ingestion.models import Chunk, ChunkMetadata
from backend.main import create_app
from backend.reasoning.structured_output import QueryResponse, VerificationResult
from backend.retrieval.hybrid_engine import RetrievalResult


def test_health_endpoint():
	with TestClient(create_app()) as client:
		resp = client.get("/api/health")
		assert resp.status_code == 200
		assert resp.json()["status"] == "ok"


def test_query_returns_valid_response_structure():
	with TestClient(create_app()) as client:
		body = {"query": "What is RAG?", "mode": "auto", "filters": {}, "options": {}}
		resp = client.post("/api/query", json=body)
		assert resp.status_code == 200
		payload = resp.json()
		assert "answer" in payload
		assert "query" in payload


def _chunk(text: str, chunk_id: str, doc_id: str = "doc-1") -> Chunk:
	return Chunk(
		text=text,
		metadata=ChunkMetadata(
			doc_id=doc_id,
			chunk_id=chunk_id,
			source_file="src",
			section="s",
			page_start=1,
			page_end=1,
			char_start=0,
			char_end=len(text),
			chunk_index=0,
			total_chunks=1,
		),
	)


def test_query_adaptive_retries_when_quality_is_low(monkeypatch):
	with TestClient(create_app()) as client:
		calls = {"retrieve": 0}

		async def fake_retrieve(**kwargs):
			_ = kwargs
			calls["retrieve"] += 1
			if calls["retrieve"] == 1:
				chunk = _chunk("irrelevant gardening notes", "c-low")
				return RetrievalResult(
					chunks=[chunk],
					retrieval_scores={chunk.metadata.chunk_id: 0.1},
					source_breakdown={"vector": 1},
					latency_ms=1.0,
				)
			chunk = _chunk("RAG combines retrieval with generation", "c-high")
			return RetrievalResult(
				chunks=[chunk],
				retrieval_scores={chunk.metadata.chunk_id: 0.9},
				source_breakdown={"vector": 1},
				latency_ms=1.0,
			)

		quality_seq = [
			QualityMetrics(
				relevance_score=0.1,
				diversity_score=0.2,
				coverage_score=0.1,
				completeness_score=0.2,
				overall_quality=0.2,
				issues=["low_relevance"],
			),
			QualityMetrics(
				relevance_score=0.9,
				diversity_score=0.8,
				coverage_score=0.9,
				completeness_score=0.8,
				overall_quality=0.88,
				issues=[],
			),
		]

		def fake_score(query, query_embedding, results):
			_ = query
			_ = query_embedding
			_ = results
			return quality_seq.pop(0) if quality_seq else QualityMetrics(
				relevance_score=0.9,
				diversity_score=0.8,
				coverage_score=0.9,
				completeness_score=0.8,
				overall_quality=0.88,
				issues=[],
			)

		async def fake_generate(query, analysis, chunks, reasoning_trace=None):
			_ = analysis
			answer = chunks[0].text if chunks else ""
			return QueryResponse(
				query_id=f"q-{uuid4().hex}",
				query=query,
				answer=answer,
				answer_summary=answer,
				answer_type="factual",
				citations=[],
				sub_questions=None,
				reasoning_trace=reasoning_trace,
				confidence="MEDIUM",
				grounding_score=0.0,
				retrieval_quality=0.0,
				warnings=[],
				latency_ms=1.0,
				token_usage={},
				model_used="test-model",
				corrective_iterations=0,
				cached=False,
			)

		async def fake_verify(query, answer, retrieved_chunks):
			_ = query
			_ = answer
			_ = retrieved_chunks
			return VerificationResult(
				passed=True,
				issues=[],
				corrective_action="none",
				grounding_score=0.9,
				citation_accuracy=1.0,
			)

		monkeypatch.setattr(client.app.state.retrieval_engine, "retrieve", fake_retrieve)
		monkeypatch.setattr(client.app.state.services["quality_scorer"], "score", fake_score)
		monkeypatch.setattr(client.app.state.services["answer_generator"], "generate", fake_generate)
		monkeypatch.setattr(client.app.state.services["verifier"], "verify", fake_verify)

		resp = client.post(
			"/api/query",
			json={
				"query": "What is RAG?",
				"mode": "auto",
				"filters": {},
				"options": {"enable_adaptive": True, "enable_verification": True},
			},
		)

		assert resp.status_code == 200
		payload = resp.json()
		assert calls["retrieve"] >= 2
		assert payload["corrective_iterations"] >= 1
		assert any("Adaptive retry attempt" in w for w in payload["warnings"])

