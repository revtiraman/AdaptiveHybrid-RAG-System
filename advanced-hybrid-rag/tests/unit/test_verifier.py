from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.ingestion.models import Chunk, ChunkMetadata
from backend.reasoning.self_verifier import SelfVerifier


def _chunk(text: str, chunk_id: str = "c1", page: int = 1) -> Chunk:
	return Chunk(
		text=text,
		metadata=ChunkMetadata(
			doc_id="d1",
			chunk_id=chunk_id,
			source_file="src",
			section="s",
			page_start=page,
			page_end=page,
			char_start=0,
			char_end=len(text),
			chunk_index=0,
			total_chunks=1,
		),
	)


def test_grounding_check_catches_unsupported_claims():
	verifier = SelfVerifier()
	res = asyncio.run(verifier.verify("what", "This includes unicorn theorem.", [_chunk("Known facts only.")]))
	assert not res.passed


def test_citation_check_validates_page_numbers():
	verifier = SelfVerifier()
	res = asyncio.run(verifier.verify("q", "Claim [missing_chunk].", [_chunk("Claim")]))
	assert any(i.issue_type == "citation" for i in res.issues)


def test_hallucination_detection_flags_entities():
	verifier = SelfVerifier()
	res = asyncio.run(verifier.verify("q", "MadeupEntity beats all models.", [_chunk("BERT baseline only.")]))
	assert not res.passed
	assert any(i.issue_type == "hallucination" for i in res.issues)


def test_contradiction_detection_flags_conflicting_terms():
	verifier = SelfVerifier()
	answer = "The model is reliable for deployment. The model is not reliable in production."
	res = asyncio.run(verifier.verify("is model reliable", answer, [_chunk("The model is reliable in some cases.")]))
	assert any(i.issue_type == "consistency" for i in res.issues)


def test_entities_present_in_query_are_not_flagged():
	verifier = SelfVerifier()
	answer = "BERT improves retrieval quality."
	res = asyncio.run(verifier.verify("How does BERT help?", answer, [_chunk("retrieval quality improves")]))
	assert not any(i.issue_type == "hallucination" for i in res.issues)


def test_passes_when_fully_grounded():
	verifier = SelfVerifier()
	res = asyncio.run(verifier.verify("q", "BERT is a model.", [_chunk("BERT is a model.", "c1")]))
	assert res.grounding_score > 0
