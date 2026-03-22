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
	quality_scorer = services.get("quality_scorer")
	adaptive_controller = services.get("adaptive_controller")
	corrective_rag = services.get("corrective_rag")
	settings = services.get("settings")
	planner = getattr(request.app.state, "query_planning_agent", None)

	analysis = analyzer.analyze(body.query)
	reasoning_trace = [f"mode={analysis.suggested_mode}"]
	if planner and (body.options.enable_planning or body.mode in {"multihop", "comparison"}):
		try:
			plan_result = await planner.run(body.query)
			reasoning_trace.extend([f"plan:{s.action}" for s in plan_result.steps])
		except Exception:
			reasoning_trace.append("plan:failed")
	async def _run_cycle(
		active_query: str,
		use_hyde: bool,
		use_graph: bool,
		use_colbert: bool,
		trace: list[str],
	):
		active_embedding = embedder.embed_query(active_query)
		retrieval = await retrieval_engine.retrieve(
			query=active_query,
			query_embedding=active_embedding,
			k_final=body.options.max_sources,
			filters=services["retrieval_filters_model"](**body.filters.model_dump()),
			use_hyde=use_hyde,
			use_graph=use_graph,
			use_colbert=use_colbert,
		)

		response = await answer_generator.generate(
			query=body.query,
			analysis=analysis,
			chunks=retrieval.chunks,
			reasoning_trace=trace,
		)
		response.retrieval_quality = sum(retrieval.retrieval_scores.values()) / max(1, len(retrieval.retrieval_scores))

		verification = None
		if body.options.enable_verification:
			verification = await verifier.verify(body.query, response.answer, retrieval.chunks)
			response.grounding_score = verification.grounding_score
			if not verification.passed:
				response.warnings.extend([i.detail for i in verification.issues])

		return retrieval, response, verification, active_embedding

	retrieval, response, verify, query_emb = await _run_cycle(
		active_query=body.query,
		use_hyde=body.options.use_hyde,
		use_graph=body.options.use_graph,
		use_colbert=body.options.use_colbert,
		trace=reasoning_trace + ["retrieve", "generate"],
	)

	adaptive_cfg = getattr(settings, "adaptive", None)
	adaptive_allowed = bool(
		body.options.enable_adaptive
		and adaptive_cfg is not None
		and adaptive_cfg.adaptive_enabled
		and quality_scorer is not None
		and adaptive_controller is not None
	)

	if adaptive_allowed:
		max_retries = max(0, int(adaptive_cfg.max_corrective_retries))
		quality_threshold = float(adaptive_cfg.quality_threshold)

		for attempt in range(1, max_retries + 1):
			quality = quality_scorer.score(body.query, query_emb, retrieval.chunks)
			verification_passed = verify is None or verify.passed
			if quality.overall_quality >= quality_threshold and verification_passed:
				break

			params = await adaptive_controller.optimize_retrieval(
				query=body.query,
				initial_results=retrieval,
				quality=quality,
				attempt=attempt,
			)

			retrieval, response, verify, query_emb = await _run_cycle(
				active_query=params.query,
				use_hyde=body.options.use_hyde or params.use_hyde,
				use_graph=body.options.use_graph and params.use_graph,
				use_colbert=body.options.use_colbert or params.use_colbert,
				trace=reasoning_trace + [f"adaptive_retry={attempt}", "retrieve", "generate"],
			)
			response.corrective_iterations = attempt
			response.warnings.append(f"Adaptive retry attempt {attempt} applied.")

	if adaptive_allowed and corrective_rag is not None and verify is not None and not verify.passed and verify.corrective_action != "none":
		corrected = await corrective_rag.run(body.query, response.model_dump(), retrieval.chunks)
		if isinstance(corrected.get("answer"), str) and corrected["answer"].strip() and corrected["answer"] != response.answer:
			response.answer = corrected["answer"]
			response.answer_summary = (response.answer[:180] + "...") if len(response.answer) > 180 else response.answer
			response.corrective_iterations += 1
		response.warnings = list(dict.fromkeys(corrected.get("warnings", response.warnings)))
		if isinstance(corrected.get("corrective_labels"), dict):
			response.warnings.append(f"Corrective labels: {corrected['corrective_labels']}")

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
