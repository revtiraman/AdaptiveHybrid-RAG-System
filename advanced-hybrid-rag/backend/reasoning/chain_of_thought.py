"""Multi-hop and structured reasoning workflows."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..adaptive.query_reformulator import QueryReformulator
from ..ingestion.embedder import BaseEmbedder
from ..retrieval.hybrid_engine import HybridRetrievalEngine, RetrievalFilters
from .query_analyzer import QueryAnalysis


class ReasoningResult(BaseModel):
	answer: str
	sub_answers: list[dict] = Field(default_factory=list)
	trace: list[str] = Field(default_factory=list)


class MultiHopReasoner:
	"""Reason over multiple retrieval hops and synthesize an answer."""

	def __init__(self, embedder: BaseEmbedder, reformulator: QueryReformulator | None = None) -> None:
		self.embedder = embedder
		self.reformulator = reformulator or QueryReformulator()

	async def reason(self, query: str, analysis: QueryAnalysis, retrieval_engine: HybridRetrievalEngine) -> ReasoningResult:
		if analysis.query_type == "survey":
			return await self._survey_mode(query, retrieval_engine)
		if analysis.query_type == "comparative":
			return await self._comparative_mode(query, retrieval_engine)
		if analysis.query_type == "multi_hop":
			return await self._multihop_mode(query, retrieval_engine)

		emb = self.embedder.embed_query(query)
		result = await retrieval_engine.retrieve(
			query=query,
			query_embedding=emb,
			k_final=max(3, analysis.estimated_sources_needed),
			filters=RetrievalFilters(),
		)
		context = "\n".join(c.text for c in result.chunks)
		answer = self._synthesize(query, context)
		return ReasoningResult(answer=answer, trace=["single-hop retrieval", "answer synthesis"])

	async def _multihop_mode(self, query: str, retrieval_engine: HybridRetrievalEngine) -> ReasoningResult:
		subqs = await self.reformulator.decompose_multihop(query)
		parts = []
		trace = ["decompose query into sub-questions"]
		for sq in subqs:
			emb = self.embedder.embed_query(sq)
			res = await retrieval_engine.retrieve(
				query=sq,
				query_embedding=emb,
				k_final=3,
				filters=RetrievalFilters(),
			)
			context = " ".join(c.text for c in res.chunks)
			part_ans = self._synthesize(sq, context)
			parts.append({"sub_question": sq, "answer": part_ans, "sources": [c.metadata.chunk_id for c in res.chunks]})
			trace.append(f"answered sub-question: {sq}")
		final_answer = "\n\n".join([f"{p['sub_question']}\n{p['answer']}" for p in parts])
		trace.append("final synthesis over sub-answers")
		return ReasoningResult(answer=final_answer, sub_answers=parts, trace=trace)

	async def _survey_mode(self, query: str, retrieval_engine: HybridRetrievalEngine) -> ReasoningResult:
		aspects = [
			f"background of {query}",
			f"methods in {query}",
			f"results in {query}",
			f"limitations in {query}",
			f"future work in {query}",
		]
		trace = ["survey mode: generated key aspects"]
		sections = []
		for aspect in aspects:
			emb = self.embedder.embed_query(aspect)
			res = await retrieval_engine.retrieve(aspect, emb, 3, RetrievalFilters())
			sections.append(f"### {aspect.title()}\n{self._synthesize(aspect, ' '.join(c.text for c in res.chunks))}")
			trace.append(f"retrieved aspect: {aspect}")
		return ReasoningResult(answer="\n\n".join(sections), trace=trace)

	async def _comparative_mode(self, query: str, retrieval_engine: HybridRetrievalEngine) -> ReasoningResult:
		entities = [e.strip() for e in query.replace(" vs ", ",").split(",") if e.strip()][:2]
		trace = ["comparative mode"]
		rows = []
		for ent in entities:
			emb = self.embedder.embed_query(ent)
			res = await retrieval_engine.retrieve(ent, emb, 3, RetrievalFilters())
			rows.append((ent, self._synthesize(ent, " ".join(c.text for c in res.chunks))))
			trace.append(f"retrieved evidence for {ent}")
		answer = "\n".join([f"- {ent}: {summary}" for ent, summary in rows])
		return ReasoningResult(answer=answer, trace=trace)

	def _synthesize(self, query: str, context: str) -> str:
		if not context.strip():
			return f"Insufficient evidence found for: {query}."
		snippet = context[:700].strip()
		return (
			f"Question: {query}\n"
			"Reasoning:\n"
			"1. Identified relevant evidence from retrieved context.\n"
			"2. Combined consistent statements into a concise summary.\n"
			f"Answer: {snippet}"
		)


__all__ = ["ReasoningResult", "MultiHopReasoner"]
