"""Query API routes for synchronous and streaming answers."""

from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ...reasoning.query_analyzer import QueryAnalyzer

router = APIRouter(prefix="/api/query", tags=["query"])


class QueryFilters(BaseModel):
	paper_ids: list[str] = Field(default_factory=list)
	year_range: tuple[int, int] | None = None
	sections: list[str] = Field(default_factory=list)
	min_relevance: float = 0.0


class QueryOptions(BaseModel):
	use_hyde: bool = False
	use_graph: bool = True
	use_colbert: bool = False
	enable_planning: bool = False
	enable_adaptive: bool = True
	enable_verification: bool = True
	citation_style: str = "inline"
	max_sources: int = 5
	stream: bool = False
	model: str | None = None


class QueryBody(BaseModel):
	query: str
	mode: Literal["auto", "basic", "multihop", "comparison"] = "auto"
	filters: QueryFilters = Field(default_factory=QueryFilters)
	options: QueryOptions = Field(default_factory=QueryOptions)


@router.post("")
async def query(request: Request, body: QueryBody):
	services = request.app.state.services
	analyzer: QueryAnalyzer = services["analyzer"]
	retrieval_engine = services["retrieval_engine"]
	answer_generator = services["answer_generator"]
	verifier = services["verifier"]
	embedder = services["embedder"]
	planner = getattr(request.app.state, "query_planning_agent", None)

	analysis = analyzer.analyze(body.query)
	reasoning_trace = [f"mode={analysis.suggested_mode}"]
	if planner and (body.options.enable_planning or body.mode in {"multihop", "comparison"}):
		try:
			plan_result = await planner.run(body.query)
			reasoning_trace.extend([f"plan:{s.action}" for s in plan_result.steps])
		except Exception:
			reasoning_trace.append("plan:failed")
	query_emb = embedder.embed_query(body.query)
	retrieval = await retrieval_engine.retrieve(
		query=body.query,
		query_embedding=query_emb,
		k_final=body.options.max_sources,
		filters=services["retrieval_filters_model"](**body.filters.model_dump()),
		use_hyde=body.options.use_hyde,
		use_graph=body.options.use_graph,
		use_colbert=body.options.use_colbert,
	)

	response = await answer_generator.generate(
		query=body.query,
		analysis=analysis,
		chunks=retrieval.chunks,
		reasoning_trace=reasoning_trace + ["retrieve", "generate"],
	)
	response.retrieval_quality = sum(retrieval.retrieval_scores.values()) / max(1, len(retrieval.retrieval_scores))

	if body.options.enable_verification:
		verify = await verifier.verify(body.query, response.answer, retrieval.chunks)
		response.grounding_score = verify.grounding_score
		if not verify.passed:
			response.warnings.extend([i.detail for i in verify.issues])

	return response.model_dump()


@router.post("/stream")
async def query_stream(request: Request, body: QueryBody):
	return StreamingResponse(_event_stream(request, body), media_type="text/event-stream")


@router.get("/stream")
async def query_stream_get(
	request: Request,
	query: str,
	mode: Literal["auto", "basic", "multihop", "comparison"] = "auto",
	max_sources: int = Query(default=5, ge=1, le=20),
	use_hyde: bool = False,
	use_graph: bool = True,
	use_colbert: bool = False,
	enable_planning: bool = False,
	enable_verification: bool = True,
	enable_adaptive: bool = True,
	citation_style: str = "inline",
	model: str | None = None,
):
	body = QueryBody(
		query=query,
		mode=mode,
		filters=QueryFilters(),
		options=QueryOptions(
			max_sources=max_sources,
			use_hyde=use_hyde,
			use_graph=use_graph,
			use_colbert=use_colbert,
			enable_planning=enable_planning,
			enable_verification=enable_verification,
			enable_adaptive=enable_adaptive,
			citation_style=citation_style,
			model=model,
		),
	)
	return StreamingResponse(_event_stream(request, body), media_type="text/event-stream")


async def _event_stream(request: Request, body: QueryBody):
	yield "data: " + json.dumps({"type": "status", "message": "Retrieving..."}) + "\n\n"
	result = await query(request, body)
	answer = result.get("answer", "")
	for token in answer.split():
		yield "data: " + json.dumps({"type": "chunk", "text": token + " "}) + "\n\n"
	for citation in result.get("citations", []):
		yield "data: " + json.dumps({"type": "citation", "citation": citation}) + "\n\n"
	yield "data: " + json.dumps({"type": "complete", "response": result}) + "\n\n"


__all__ = ["router", "QueryBody", "QueryFilters", "QueryOptions"]
