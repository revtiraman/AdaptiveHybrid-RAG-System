from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.adaptive.corrective_rag import CorrectiveRAG
from backend.ingestion.models import Chunk, ChunkMetadata


def _chunk(text: str, chunk_id: str = "c1") -> Chunk:
	return Chunk(
		text=text,
		metadata=ChunkMetadata(
			doc_id="d1",
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


async def _refine(query: str, bad_chunks: list[Chunk]) -> list[Chunk]:
	_ = query
	_ = bad_chunks
	return [_chunk("relevant retrieval evidence", "refined")]


async def _regen(query: str, chunks: list[Chunk]) -> dict:
	_ = query
	return {"answer": f"regenerated from {len(chunks)} chunk(s)", "warnings": []}


def test_classification_returns_irrelevant_for_zero_overlap():
	crag = CorrectiveRAG()
	label = crag.classify_chunk("deep learning", _chunk("medieval pottery catalog"))
	assert label == "IRRELEVANT"


def test_classification_returns_contradictory_for_negation_conflict():
	crag = CorrectiveRAG()
	label = crag.classify_chunk("model is robust", _chunk("model is not robust under noise"))
	assert label == "CONTRADICTORY"


def test_run_triggers_regeneration_when_bad_majority():
	crag = CorrectiveRAG(regenerate_answer=_regen, refine_retrieval=_refine)
	chunks = [
		_chunk("unrelated gardening notes", "a"),
		_chunk("historical pottery details", "b"),
		_chunk("model is not robust", "c"),
	]
	result = asyncio.run(crag.run("model is robust", {"answer": "initial", "warnings": []}, chunks))
	assert "Corrective RAG regeneration applied." in result["warnings"]
	assert "corrective_labels" in result


def test_run_keeps_initial_result_when_chunks_are_mostly_correct():
	crag = CorrectiveRAG()
	chunks = [
		_chunk("retrieval model robust performance", "a"),
		_chunk("model robust benchmark results", "b"),
	]
	result = asyncio.run(crag.run("model robust retrieval", {"answer": "initial", "warnings": []}, chunks))
	assert "Corrective RAG check passed without re-retrieval." in result["warnings"]
	assert result["corrective_labels"].get("CORRECT", 0) >= 1
